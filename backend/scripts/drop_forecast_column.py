# drop_forecast_column.py
# calendar_events에서 forecast(시장 컨센서스 예상값) 컬럼을 삭제한다. FRED/KIS/DART 중
# 어느 소스도 이 값을 제공하지 않아서 스키마에 있는 동안 한 번도 실제 값이 들어간 적이
# 없었다(항상 None) - schemas/calendar.py·models/calendar.py에서도 필드를 제거했다.
#
# 실행: backend/ 디렉토리에서 `uv run python scripts/drop_forecast_column.py`

import asyncio

from sqlalchemy import text

from backend.core.database import async_session


async def main() -> None:
    async with async_session() as session:
        await session.execute(text("ALTER TABLE calendar_events DROP COLUMN IF EXISTS forecast"))
        await session.commit()
        print("=== calendar_events.forecast 컬럼 삭제 완료 ===")


if __name__ == "__main__":
    asyncio.run(main())
