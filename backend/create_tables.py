# create_tables.py
# 모델 정의를 보고 Supabase에 테이블을 만드는 일회성 스크립트

import asyncio
import sys

sys.path.insert(0, "src")

from backend.core.database import Base, get_engine
from backend.domain.timeline.models import timeline  # noqa: F401 - 모델 등록용


async def main():
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("테이블 생성 완료")


asyncio.run(main())
