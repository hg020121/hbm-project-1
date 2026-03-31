# api/routers/hbm.py
# REST API 엔드포인트 (수업 routers/task_a.py 구조 기반)

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

import api.cruds.hbm as crud
import api.schemas.hbm as schema
from api.db import get_db
from api.services.ai_service import (
    recommend_process_params,
    chat_with_context,
    analyze_process_image,
    upload_pdf_to_vectorstore,
    query_rag,
)
from api.services.dummy_service import generate_dummy_lots

router = APIRouter()


# ============================
# 대시보드 통계
# ============================
@router.get("/dashboard", response_model=schema.DashboardStats, tags=["대시보드"])
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    stats = await crud.get_dashboard_stats(db)
    return schema.DashboardStats(**stats)


# ============================
# Engineer
# ============================
@router.get("/engineers", response_model=List[schema.EngineerResponse], tags=["엔지니어"])
async def list_engineers(db: AsyncSession = Depends(get_db)):
    return await crud.get_all_engineers(db)


# ============================
# LOT (수업 /tasks 패턴 그대로)
# ============================
@router.get("/lots", response_model=List[schema.LotResponse], tags=["LOT"])
async def list_lots(
    response: Response,
    status: Optional[str] = Query(None, description="lot_status 필터"),
    db: AsyncSession = Depends(get_db),
):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return await crud.get_all_lots(db, status=status)


@router.get("/lots/{lot_id}", response_model=schema.LotResponse, tags=["LOT"])
async def get_lot(lot_id: str, db: AsyncSession = Depends(get_db)):
    lot = await crud.get_lot(db, lot_id)
    if lot is None:
        raise HTTPException(status_code=404, detail=f"LOT {lot_id}를 찾을 수 없습니다.")
    return lot


@router.post("/lots", response_model=schema.LotResponse, tags=["LOT"])
async def create_lot(lot_body: schema.LotCreate, db: AsyncSession = Depends(get_db)):
    lot = await crud.create_lot(db, lot_body)
    await db.commit()
    await db.refresh(lot)
    return lot


@router.put("/lots/{lot_id}/status", response_model=schema.LotResponse, tags=["LOT"])
async def update_lot_status(
    lot_id: str,
    body: schema.LotStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    lot = await crud.update_lot_status(db, lot_id, body.lot_status)
    if lot is None:
        raise HTTPException(status_code=404, detail=f"LOT {lot_id}를 찾을 수 없습니다.")
    await db.commit()
    return lot


# ============================
# LOT 전체 공정 이력
# ============================
@router.get("/lots/{lot_id}/history", response_model=schema.LotFullHistory, tags=["LOT"])
async def get_lot_history(lot_id: str, db: AsyncSession = Depends(get_db)):
    lot = await crud.get_lot(db, lot_id)
    if lot is None:
        raise HTTPException(status_code=404, detail=f"LOT {lot_id}를 찾을 수 없습니다.")
    return schema.LotFullHistory(
        lot=schema.LotResponse.model_validate(lot),
        incoming=schema.IncomingResponse.model_validate(inc) if (inc := await crud.get_incoming(db, lot_id)) else None,
        pre_analysis=schema.PreAnalysisResponse.model_validate(pre) if (pre := await crud.get_pre_analysis(db, lot_id)) else None,
        ai_recommends=[schema.AiRecommendResponse.model_validate(r) for r in await crud.get_recommends_by_lot(db, lot_id)],
        stackings=[schema.StackingResponse.model_validate(s) for s in await crud.get_stackings_by_lot(db, lot_id)],
        reflows=[schema.ReflowResponse.model_validate(r) for r in await crud.get_reflows_by_lot(db, lot_id)],
        injection=schema.InjectionResponse.model_validate(inj) if (inj := await crud.get_injection(db, lot_id)) else None,
        result=schema.ResultResponse.model_validate(res) if (res := await crud.get_result(db, lot_id)) else None,
    )


# ============================
# 공정 데이터 등록
# ============================
@router.post("/lots/{lot_id}/incoming", response_model=schema.IncomingResponse, tags=["공정"])
async def create_incoming(lot_id: str, body: schema.IncomingCreate, db: AsyncSession = Depends(get_db)):
    body.lot_id = lot_id
    inc = await crud.create_incoming(db, body)
    await crud.update_lot_status(db, lot_id, "INCOMING")
    await db.commit()
    return inc


@router.post("/lots/{lot_id}/pre-analysis", response_model=schema.PreAnalysisResponse, tags=["공정"])
async def create_pre_analysis(lot_id: str, body: schema.PreAnalysisCreate, db: AsyncSession = Depends(get_db)):
    body.lot_id = lot_id
    pre = await crud.create_pre_analysis(db, body)
    await crud.update_lot_status(db, lot_id, "PRE_ANALYSIS")
    await db.commit()
    return pre


@router.post("/lots/{lot_id}/stacking", response_model=schema.StackingResponse, tags=["공정"])
async def create_stacking(lot_id: str, body: schema.StackingCreate, db: AsyncSession = Depends(get_db)):
    body.lot_id = lot_id
    stk = await crud.create_stacking(db, body)
    await crud.update_lot_status(db, lot_id, f"STACKING_{body.stack_seq}")
    await db.commit()
    return stk


@router.post("/lots/{lot_id}/reflow", response_model=schema.ReflowResponse, tags=["공정"])
async def create_reflow(lot_id: str, body: schema.ReflowCreate, db: AsyncSession = Depends(get_db)):
    body.lot_id = lot_id
    rfw = await crud.create_reflow(db, body)
    await crud.update_lot_status(db, lot_id, f"REFLOW_{body.reflow_seq}")
    await db.commit()
    return rfw


@router.post("/lots/{lot_id}/injection", response_model=schema.InjectionResponse, tags=["공정"])
async def create_injection(lot_id: str, body: schema.InjectionCreate, db: AsyncSession = Depends(get_db)):
    body.lot_id = lot_id
    inj = await crud.create_injection(db, body)
    await crud.update_lot_status(db, lot_id, "INJECTION")
    await db.commit()
    return inj


@router.post("/lots/{lot_id}/result", response_model=schema.ResultResponse, tags=["공정"])
async def create_result(lot_id: str, body: schema.ResultCreate, db: AsyncSession = Depends(get_db)):
    body.lot_id = lot_id
    res = await crud.create_result(db, body)
    await crud.update_lot_status(db, lot_id, "DONE")
    await db.commit()
    return res


# ============================
# AI 추천 (Phase 2-1)
# ============================
@router.post("/lots/{lot_id}/recommend", response_model=schema.AiRecommendResponse, tags=["AI"])
async def ai_recommend(lot_id: str, db: AsyncSession = Depends(get_db)):
    lot = await crud.get_lot(db, lot_id)
    if lot is None:
        raise HTTPException(status_code=404, detail=f"LOT {lot_id}를 찾을 수 없습니다.")

    incoming = await crud.get_incoming(db, lot_id)
    if incoming is None:
        raise HTTPException(status_code=400, detail="입고 데이터가 없습니다.")

    stackings = await crud.get_stackings_by_lot(db, lot_id)
    stack_history = [{"seq": s.stack_seq, "pressure": s.pressure, "void": s.void_area_pct} for s in stackings]
    current_void = stackings[-1].void_area_pct if stackings else None
    current_seq = len(stackings) + 1

    similar_lots = await crud.get_similar_lots_by_material(db, incoming.viscosity, incoming.cte)

    result = await recommend_process_params(
        lot_id=lot_id,
        current_viscosity=incoming.viscosity,
        current_cte=incoming.cte,
        current_stack_seq=current_seq,
        current_void=current_void,
        similar_lots=similar_lots,
        stack_history=stack_history,
    )

    rec = await crud.create_recommend(
        db, lot_id,
        pressure=result["recommend_pressure"],
        temp=result["recommend_temp"],
    )
    await db.commit()

    return schema.AiRecommendResponse(
        recommend_id=rec.recommend_id,
        lot_id=rec.lot_id,
        recommend_pressure=rec.recommend_pressure,
        recommend_temp=rec.recommend_temp,
        recommended_at=rec.recommended_at,
        reason=result.get("reason"),
    )


# ============================
# AI 챗봇 (Phase 2-2)
# ============================
@router.post("/chat", response_model=schema.ChatResponse, tags=["AI"])
async def chat(body: schema.ChatRequest, db: AsyncSession = Depends(get_db)):
    lot_context = None
    if body.lot_id:
        lot = await crud.get_lot(db, body.lot_id)
        if lot:
            incoming = await crud.get_incoming(db, body.lot_id)
            stackings = await crud.get_stackings_by_lot(db, body.lot_id)
            lot_context = {
                "lot_id": lot.lot_id,
                "lot_status": lot.lot_status,
                "viscosity": incoming.viscosity if incoming else None,
                "cte": incoming.cte if incoming else None,
                "stack_count": len(stackings),
                "current_void": stackings[-1].void_area_pct if stackings else None,
            }

    rag_ctx = None
    if VECTORSTORE_EXISTS():
        rag_result = await query_rag(body.message, top_k=2)
        rag_ctx = rag_result.get("answer", "")

    response = await chat_with_context(body.message, body.role, lot_context, rag_ctx)
    return schema.ChatResponse(message=body.message, response=response)


def VECTORSTORE_EXISTS():
    import os
    from api.services.ai_service import FAISS_DIR
    return os.path.exists(FAISS_DIR)


# ============================
# 이미지 분석 (Phase 2-3)
# ============================
@router.post("/analyze-image", response_model=schema.ImageAnalysisResponse, tags=["AI"])
async def analyze_image(
    file: UploadFile = File(...),
    lot_id: Optional[str] = Query(None),
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")
    image_bytes = await file.read()
    result = await analyze_process_image(image_bytes, lot_id)
    return schema.ImageAnalysisResponse(
        lot_id=lot_id,
        void_estimate=result.get("void_estimate"),
        layer_voids=result.get("layer_voids"),
        defect_locations=result.get("defect_locations"),
        severity=result.get("severity"),
        analysis=result.get("analysis", ""),
        recommendation=result.get("recommendation", ""),
    )


# ============================
# PDF RAG (Phase 2-4)
# ============================
@router.post("/upload-pdf", response_model=schema.PdfUploadResponse, tags=["RAG"])
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="PDF 파일만 업로드 가능합니다.")
    file_bytes = await file.read()
    result = await upload_pdf_to_vectorstore(file_bytes, file.filename)
    return schema.PdfUploadResponse(**result)


@router.post("/rag-query", response_model=schema.RagQueryResponse, tags=["RAG"])
async def rag_query(body: schema.RagQueryRequest):
    result = await query_rag(body.question, body.top_k)
    return schema.RagQueryResponse(**result)


# ============================
# 더미 데이터 생성
# ============================
@router.post("/generate-dummy", tags=["데이터"])
async def generate_dummy(body: schema.GenerateDummyRequest, db: AsyncSession = Depends(get_db)):
    result = await generate_dummy_lots(db, count=body.count, yield_rate=body.yield_rate)
    return result
