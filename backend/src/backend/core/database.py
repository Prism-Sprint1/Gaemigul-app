# database.py
# DB 엔진 생성 (처음 쓸 때 만든다)
# 세션 창구 생성
# ORM 모델이 상속받을 Base
# FastAPI 의존성(Dependency) - DB 세션
#
# 엔진을 import 시점에 만들지 않고 함수로 감싼 이유:
#   전에는 이 파일을 읽는 순간 DATABASE_URL을 검사하고 엔진을 만들었다. 그러면 이 파일을
#   import하는 코드가 하나라도 있으면 DATABASE_URL이 없는 팀원은 서버를 아예 못 띄운다.
#   config.py의 정책(키가 없어도 앱은 뜨고, 그 키를 실제로 쓸 때만 에러)과 어긋나서 함수로 바꿨다.
#
# 그래서 DB를 쓰는 코드는 engine이나 async_session을 직접 참조하지 말고 아래 함수를 부를 것

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from backend.core.config import get_settings


# ORM 모델(엔티티)들이 상속받을 공통 Base 클래스
# DB 연결과 무관하므로 DATABASE_URL이 없어도 이 클래스는 쓸 수 있다 (모델 파일 import가 안 깨진다)
class Base(DeclarativeBase):
    pass


# DB 엔진을 한 번만 만들어서 재사용
# echo를 True로 바꾸면 실행되는 SQL이 전부 터미널에 찍힌다 - 쿼리를 확인할 때만 켤 것
#   (슬롯 하나 저장에 30줄 넘게 들어가서, 켜두면 정작 봐야 할 에러 메시지가 묻힌다)
@lru_cache
def get_engine() -> AsyncEngine:
    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL이 .env에 없습니다. backend/.env에 추가해주세요.")

    return create_async_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True,  # 끊어진 DB 연결 자동 감지 및 재연결
        pool_recycle=300,  # 5분 이상 비활성화된 커넥션 자동 재활성화 (Supabase 타임아웃 방지)
    )


# 실제 DB 작업을 수행할 비동기 세션 창구
@lru_cache
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=get_engine(), class_=AsyncSession, expire_on_commit=False)


# FastAPI 엔드포인트에서 사용할 DB 세션 의존성(Dependency)
# 라우터 함수에 session: AsyncSession = Depends(get_db) 형태로 받아서 쓴다
async def get_db():
    async with get_session_factory()() as session:
        yield session
