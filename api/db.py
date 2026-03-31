# api/db.py
# 수업 파일(db_a.py) 구조 기반, hbm_integrated_db 연결

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncAttrs
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import text
from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "53301")
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "SqlDba-1")
DB_NAME = os.getenv("DB_NAME", "hbm_integrated_db")

ASYNC_DB_URL = (
    f"mysql+aiomysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
)

# Base (AsyncAttrs 지원 - 수업 방식 그대로)
Base = declarative_base(cls=AsyncAttrs)

# 비동기 엔진
async_engine = create_async_engine(
    ASYNC_DB_URL,
    echo=False,
    future=True,
    isolation_level="READ COMMITTED",
    pool_pre_ping=True,
    pool_recycle=1800,
)

# 세션 팩토리
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# FastAPI 의존성 (수업 방식 그대로)
async def get_db():
    async with AsyncSessionLocal() as session:
        await session.execute(text("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED"))
        try:
            yield session
        finally:
            await session.close()
