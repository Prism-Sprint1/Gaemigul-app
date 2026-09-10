# database.py
# DB 엔진 생성
# 세션 창구 생성
# ORM 모델이 상속받을 Base
# FastAPI 의존성(Dependency) - DB 세션

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from backend.core.config import get_settings

_settings = get_settings()

if not _settings.database_url:
    raise ValueError("DATABASE_URL이 .env 파일에 설정되지 않았습니다.")

# DB 엔진 생성
engine = create_async_engine(
    _settings.database_url,
    echo=True,
    pool_pre_ping=True,  # 끊어진 DB 연결 자동 감지 및 재연결
    pool_recycle=300,  # 5분 이상 비활성화된 커넥션 자동 재활성화 (Supabase 타임아웃 방지)
)

# 실제 DB 작업을 수행할 비동기 세션 창구 생성
async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


# ORM 모델(엔티티)들이 상속받을 공통 Base 클래스
class Base(DeclarativeBase):
    pass


# FastAPI 엔드포인트에서 사용할 DB 세션 의존성(Dependency)
async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            # async with 블록이 끝나면 세션이 자동으로 닫히지만(close),
            # 명시적인 흐름 이해를 위해 yield 구조를 유지한다
            await session.close()
