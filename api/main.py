# api/main.py
# FastAPI 앱 진입점 (수업 main.py 구조 기반)
# python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.middleware.cors import CORSMiddleware
import os

from api.routers import hbm

app = FastAPI(
    title="HBM MR-MUF 공정 AI 추천 시스템",
    description="HBM 반도체 MR-MUF 공정 데이터 기반 AI 파라미터 추천 + RAG + Vision",
    version="1.0.0",
    docs_url=None,  # 기본 /docs 비활성화 (수업 방식)
)

# CORS 설정 (Vue.js 연동)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록 (수업 include_router 방식)
app.include_router(hbm.router, prefix="/api")

# Static 파일
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def root():
    return {"message": "HBM MR-MUF 공정 AI 추천 시스템 API 서버"}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "HBM MR-MUF AI System"}


# Swagger UI 커스터마이징 (수업 방식)
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title="HBM MR-MUF AI API Docs",
    )
