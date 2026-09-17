import asyncio
import sys

sys.path.insert(0, "src")

from backend.core.database import async_session
from sqlalchemy import text


async def main():
    async with async_session() as db:
        result = await db.execute(
            text(
                "SELECT column_name, data_type FROM information_schema.columns "
                "WHERE table_name = 'calendar_events' ORDER BY ordinal_position"
            )
        )
        for row in result:
            print(row.column_name, "-", row.data_type)


asyncio.run(main())
