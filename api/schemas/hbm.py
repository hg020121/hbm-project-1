# api/schemas/hbm.py
# Pydantic 요청/응답 스키마

from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


# ============================
# Engineer
# ============================
class EngineerBase(BaseModel):
    engineer_id: str
    name: str
    dept: str

class EngineerResponse(EngineerBase):
    class Config:
        from_attributes = True


# ============================
# HBM_CARRIER_LOT
# ============================
class LotCreate(BaseModel):
    lot_id: str
    lot_status: str = "INCOMING"

class LotResponse(BaseModel):
    lot_id: str
    lot_status: str
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class LotStatusUpdate(BaseModel):
    lot_status: str


# ============================
# INCOMING
# ============================
class IncomingCreate(BaseModel):
    lot_id: str
    vendor_id: str
    viscosity: float
    cte: float
    incoming_date: date

class IncomingResponse(IncomingCreate):
    incoming_id: str
    class Config:
        from_attributes = True


# ============================
# PRE_ANALYSIS
# ============================
class PreAnalysisCreate(BaseModel):
    lot_id: str
    engineer_id: str
    measured_viscosity: float
    measured_cte: float
    measured_date: date

class PreAnalysisResponse(PreAnalysisCreate):
    pre_id: str
    class Config:
        from_attributes = True


# ============================
# AI_RECOMMEND
# ============================
class AiRecommendResponse(BaseModel):
    recommend_id: str
    lot_id: str
    recommend_pressure: float
    recommend_temp: float
    recommended_at: Optional[datetime] = None
    reason: Optional[str] = None   # GPT 추천 근거
    class Config:
        from_attributes = True


# ============================
# STACKING
# ============================
class StackingCreate(BaseModel):
    lot_id: str
    engineer_id: str
    recommend_id: str
    stack_seq: int
    pressure: float
    void_area_pct: Optional[float] = None
    stack_date: datetime

class StackingResponse(StackingCreate):
    stack_id: str
    class Config:
        from_attributes = True


# ============================
# REFLOW
# ============================
class ReflowCreate(BaseModel):
    lot_id: str
    engineer_id: str
    reflow_seq: int
    temperature: float
    reflow_date: datetime

class ReflowResponse(ReflowCreate):
    reflow_id: str
    class Config:
        from_attributes = True


# ============================
# INJECTION
# ============================
class InjectionCreate(BaseModel):
    lot_id: str
    engineer_id: str
    inject_pressure: float
    injection_date: datetime

class InjectionResponse(InjectionCreate):
    injection_id: str
    class Config:
        from_attributes = True


# ============================
# RESULT_ANALYSIS
# ============================
class ResultCreate(BaseModel):
    lot_id: str
    engineer_id: str
    void_area_pct: float
    final_result: str
    analysis_date: date

class ResultResponse(ResultCreate):
    result_id: str
    class Config:
        from_attributes = True


# ============================
# LOT 전체 공정 이력
# ============================
class LotFullHistory(BaseModel):
    lot: LotResponse
    incoming: Optional[IncomingResponse] = None
    pre_analysis: Optional[PreAnalysisResponse] = None
    ai_recommends: List[AiRecommendResponse] = []
    stackings: List[StackingResponse] = []
    reflows: List[ReflowResponse] = []
    injection: Optional[InjectionResponse] = None
    result: Optional[ResultResponse] = None


# ============================
# AI 챗봇
# ============================
class ChatRequest(BaseModel):
    message: str
    lot_id: Optional[str] = None   # LOT 컨텍스트 포함 시
    role: str = "engineer"         # engineer | quality

class ChatResponse(BaseModel):
    message: str
    response: str


# ============================
# 이미지 분석
# ============================
class ImageAnalysisResponse(BaseModel):
    lot_id: Optional[str] = None
    void_estimate: Optional[float] = None
    layer_voids: Optional[List[float]] = None
    defect_locations: Optional[str] = None
    severity: Optional[str] = None
    analysis: str
    recommendation: str


# ============================
# PDF RAG
# ============================
class PdfUploadResponse(BaseModel):
    filename: str
    chunks: int
    message: str

class RagQueryRequest(BaseModel):
    question: str
    top_k: int = 3

class RagQueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[str] = []


# ============================
# 대시보드 통계
# ============================
class DashboardStats(BaseModel):
    total_lots: int
    done_lots: int
    in_progress_lots: int
    yield_rate: float
    avg_void: float
    defect_count: int


# ============================
# 더미 데이터 생성
# ============================
class GenerateDummyRequest(BaseModel):
    count: int = 10
    yield_rate: float = 0.98
