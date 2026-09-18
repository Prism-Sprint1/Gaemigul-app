import asyncio
import sys
import traceback

sys.path.insert(0, "src")

from backend.core.database import async_session
from backend.domain.calendar.services import calendar as calendar_service


async def main():
    async with async_session() as db:
        try:
            events = await calendar_service.get_events_by_month(db, 2026, 9)
            print("OK, got", len(events), "events")
        except Exception:
            traceback.print_exc()


asyncio.run(main())
