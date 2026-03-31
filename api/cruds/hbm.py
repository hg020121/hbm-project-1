# api/cruds/hbm.py
# DB CRUD 로직 (수업 cruds/task_a.py 구조 기반)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.engine import Result
from typing import Optional, List
import api.models.hbm as model
import api.schemas.hbm as schema
from datetime import datetime, date
import uuid


def gen_id(prefix: str, num: int) -> str:
    return f"{prefix}-{num:03d}"


# ============================
# Engineer
# ============================
async def get_all_engineers(db: AsyncSession) -> List[model.Engineer]:
    result = await db.execute(select(model.Engineer).order_by(model.Engineer.engineer_id))
    return result.scalars().all()

async def get_engineer(db: AsyncSession, engineer_id: str) -> Optional[model.Engineer]:
    result = await db.execute(select(model.Engineer).where(model.Engineer.engineer_id == engineer_id))
    return result.scalar_one_or_none()


# ============================
# HBM_CARRIER_LOT
# ============================
async def get_all_lots(db: AsyncSession, status: Optional[str] = None) -> List[model.HbmCarrierLot]:
    query = select(model.HbmCarrierLot).order_by(model.HbmCarrierLot.lot_id)
    if status:
        query = query.where(model.HbmCarrierLot.lot_status == status)
    result = await db.execute(query)
    return result.scalars().all()

async def get_lot(db: AsyncSession, lot_id: str) -> Optional[model.HbmCarrierLot]:
    result = await db.execute(select(model.HbmCarrierLot).where(model.HbmCarrierLot.lot_id == lot_id))
    return result.scalar_one_or_none()

async def create_lot(db: AsyncSession, lot_create: schema.LotCreate) -> model.HbmCarrierLot:
    lot = model.HbmCarrierLot(**lot_create.model_dump())
    db.add(lot)
    await db.flush()
    await db.refresh(lot)
    return lot

async def update_lot_status(db: AsyncSession, lot_id: str, new_status: str) -> Optional[model.HbmCarrierLot]:
    lot = await get_lot(db, lot_id)
    if lot is None:
        return None
    lot.lot_status = new_status
    db.add(lot)
    await db.flush()
    await db.refresh(lot)
    return lot


# ============================
# INCOMING
# ============================
async def get_incoming(db: AsyncSession, lot_id: str) -> Optional[model.Incoming]:
    result = await db.execute(select(model.Incoming).where(model.Incoming.lot_id == lot_id))
    return result.scalar_one_or_none()

async def create_incoming(db: AsyncSession, data: schema.IncomingCreate) -> model.Incoming:
    count_result = await db.execute(select(func.count()).select_from(model.Incoming))
    count = count_result.scalar() + 1
    incoming = model.Incoming(incoming_id=gen_id("INC", count), **data.model_dump())
    db.add(incoming)
    await db.flush()
    await db.refresh(incoming)
    return incoming


# ============================
# PRE_ANALYSIS
# ============================
async def get_pre_analysis(db: AsyncSession, lot_id: str) -> Optional[model.PreAnalysis]:
    result = await db.execute(select(model.PreAnalysis).where(model.PreAnalysis.lot_id == lot_id))
    return result.scalar_one_or_none()

async def create_pre_analysis(db: AsyncSession, data: schema.PreAnalysisCreate) -> model.PreAnalysis:
    count_result = await db.execute(select(func.count()).select_from(model.PreAnalysis))
    count = count_result.scalar() + 1
    pre = model.PreAnalysis(pre_id=gen_id("PRE", count), **data.model_dump())
    db.add(pre)
    await db.flush()
    await db.refresh(pre)
    return pre


# ============================
# AI_RECOMMEND
# ============================
async def get_recommends_by_lot(db: AsyncSession, lot_id: str) -> List[model.AiRecommend]:
    result = await db.execute(
        select(model.AiRecommend)
        .where(model.AiRecommend.lot_id == lot_id)
        .order_by(model.AiRecommend.recommended_at)
    )
    return result.scalars().all()

async def create_recommend(db: AsyncSession, lot_id: str, pressure: float, temp: float) -> model.AiRecommend:
    count_result = await db.execute(select(func.count()).select_from(model.AiRecommend))
    count = count_result.scalar() + 1
    rec = model.AiRecommend(
        recommend_id=gen_id("REC", count),
        lot_id=lot_id,
        recommend_pressure=pressure,
        recommend_temp=temp,
    )
    db.add(rec)
    await db.flush()
    await db.refresh(rec)
    return rec


# ============================
# STACKING
# ============================
async def get_stackings_by_lot(db: AsyncSession, lot_id: str) -> List[model.Stacking]:
    result = await db.execute(
        select(model.Stacking)
        .where(model.Stacking.lot_id == lot_id)
        .order_by(model.Stacking.stack_seq)
    )
    return result.scalars().all()

async def create_stacking(db: AsyncSession, data: schema.StackingCreate) -> model.Stacking:
    count_result = await db.execute(select(func.count()).select_from(model.Stacking))
    count = count_result.scalar() + 1
    stk = model.Stacking(stack_id=gen_id("STK", count), **data.model_dump())
    db.add(stk)
    await db.flush()
    await db.refresh(stk)
    return stk

async def get_similar_lots_by_material(
    db: AsyncSession, viscosity: float, cte: float, limit: int = 5
) -> List[dict]:
    """유사 소재(점도/CTE 기준) 과거 LOT 공정 이력 조회 - LLM 컨텍스트용"""
    result = await db.execute(
        select(
            model.Incoming.lot_id,
            model.Incoming.viscosity,
            model.Incoming.cte,
            model.HbmCarrierLot.lot_status,
        )
        .join(model.HbmCarrierLot, model.Incoming.lot_id == model.HbmCarrierLot.lot_id)
        .where(
            and_(
                model.Incoming.viscosity.between(viscosity - 0.3, viscosity + 0.3),
                model.Incoming.cte.between(cte - 1.0, cte + 1.0),
                model.HbmCarrierLot.lot_status == "DONE",
            )
        )
        .limit(limit)
    )
    rows = result.all()
    similar = []
    for row in rows:
        stackings = await get_stackings_by_lot(db, row.lot_id)
        result_q = await db.execute(
            select(model.ResultAnalysis).where(model.ResultAnalysis.lot_id == row.lot_id)
        )
        res = result_q.scalar_one_or_none()
        similar.append({
            "lot_id": row.lot_id,
            "viscosity": row.viscosity,
            "cte": row.cte,
            "stackings": [
                {"seq": s.stack_seq, "pressure": s.pressure, "void": s.void_area_pct}
                for s in stackings
            ],
            "final_result": res.final_result if res else None,
            "final_void": res.void_area_pct if res else None,
        })
    return similar


# ============================
# REFLOW
# ============================
async def get_reflows_by_lot(db: AsyncSession, lot_id: str) -> List[model.Reflow]:
    result = await db.execute(
        select(model.Reflow)
        .where(model.Reflow.lot_id == lot_id)
        .order_by(model.Reflow.reflow_seq)
    )
    return result.scalars().all()

async def create_reflow(db: AsyncSession, data: schema.ReflowCreate) -> model.Reflow:
    count_result = await db.execute(select(func.count()).select_from(model.Reflow))
    count = count_result.scalar() + 1
    rfw = model.Reflow(reflow_id=gen_id("RFW", count), **data.model_dump())
    db.add(rfw)
    await db.flush()
    await db.refresh(rfw)
    return rfw


# ============================
# INJECTION
# ============================
async def get_injection(db: AsyncSession, lot_id: str) -> Optional[model.Injection]:
    result = await db.execute(select(model.Injection).where(model.Injection.lot_id == lot_id))
    return result.scalar_one_or_none()

async def create_injection(db: AsyncSession, data: schema.InjectionCreate) -> model.Injection:
    count_result = await db.execute(select(func.count()).select_from(model.Injection))
    count = count_result.scalar() + 1
    inj = model.Injection(injection_id=gen_id("INJ", count), **data.model_dump())
    db.add(inj)
    await db.flush()
    await db.refresh(inj)
    return inj


# ============================
# RESULT_ANALYSIS
# ============================
async def get_result(db: AsyncSession, lot_id: str) -> Optional[model.ResultAnalysis]:
    result = await db.execute(select(model.ResultAnalysis).where(model.ResultAnalysis.lot_id == lot_id))
    return result.scalar_one_or_none()

async def create_result(db: AsyncSession, data: schema.ResultCreate) -> model.ResultAnalysis:
    count_result = await db.execute(select(func.count()).select_from(model.ResultAnalysis))
    count = count_result.scalar() + 1
    res = model.ResultAnalysis(result_id=gen_id("RST", count), **data.model_dump())
    db.add(res)
    await db.flush()
    await db.refresh(res)
    return res


# ============================
# 대시보드 통계
# ============================
async def get_dashboard_stats(db: AsyncSession) -> dict:
    total = (await db.execute(select(func.count()).select_from(model.HbmCarrierLot))).scalar()
    done = (await db.execute(
        select(func.count()).select_from(model.HbmCarrierLot)
        .where(model.HbmCarrierLot.lot_status == "DONE")
    )).scalar()
    defect = (await db.execute(
        select(func.count()).select_from(model.ResultAnalysis)
        .where(model.ResultAnalysis.final_result == "사용불가")
    )).scalar()
    avg_void_row = (await db.execute(
        select(func.avg(model.ResultAnalysis.void_area_pct)).select_from(model.ResultAnalysis)
    )).scalar()
    return {
        "total_lots": total or 0,
        "done_lots": done or 0,
        "in_progress_lots": (total or 0) - (done or 0),
        "yield_rate": round(((done - defect) / done * 100) if done else 0, 2),
        "avg_void": round(avg_void_row or 0, 4),
        "defect_count": defect or 0,
    }
