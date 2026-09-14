# seed_2026_calendar.py
# FRED CPI/PPI 2026년 1~12월 데이터를 한 번에 가져와서 Supabase calendar_events에 upsert한다.
# 이미 발표된 달은 RELEASED+실제값, FRED release calendar에 예정 발표일이 확인되는 아직
# 발표 안 된 달은 SCHEDULED(actual=null)로 저장한다. 예정 발표일 자체가 없는 달은 만들지 않는다.
#
# 실행: backend/ 디렉토리에서 `uv run python scripts/seed_2026_calendar.py`
# 전제: calendar_events 테이블이 Supabase에 이미 생성되어 있어야 한다.

import asyncio

from backend.domain.calendar.services import calendar as calendar_service


async def main() -> None:
    for indicator in ("CPI", "PPI"):
        events = await calendar_service.ingest_year_from_fred(indicator, 2026)
        print(f"=== {indicator} 2026년: {len(events)}건 upsert ===")
        for event in events:
            print(
                f"  {event.id} | publishedAt={event.publishedAt} time={event.time} "
                f"| actual={event.actual} previous={event.previous} status={event.status}"
            )


if __name__ == "__main__":
    asyncio.run(main())
