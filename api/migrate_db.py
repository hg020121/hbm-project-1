# api/migrate_db.py
# DB 테이블 생성 스크립트 (수업 migrate_db_a.py 기반)
# python -m api.migrate_db

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from api.db import Base, ASYNC_DB_URL
from api.models import hbm  # 모든 모델 임포트 (테이블 인식용)


async def reset_database():
    engine = create_async_engine(ASYNC_DB_URL, echo=True)
    async with engine.begin() as conn:
        print("기존 테이블 삭제 중...")
        await conn.run_sync(Base.metadata.drop_all)
        print("테이블 생성 중...")
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("✅ DB 초기화 완료!")
    print("다음 단계: step3.sql, step4.sql을 MariaDB에서 실행하여 데이터를 채워주세요.")


if __name__ == "__main__":
    asyncio.run(reset_database())
