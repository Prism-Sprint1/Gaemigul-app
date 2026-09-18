# seed_fomc_2026.py
#
# 미국 FOMC(연방공개시장위원회) 2026년 일정을 Supabase calendar_events에 upsert한다.
# core/fed_client.py의 정적 표(federalreserve.gov 공식 캘린더)를 소스로 STATEMENT(금리결정,
# 8건 전체)/SEP(경제전망, SEP 동반 회의만)/MINUTES(의사록, 공식 공개일이 확인된 회의만) 이벤트를
# 만든다. FOMC_MEETING(회의 기간)과 FOMC_PRESS_CONFERENCE(기자회견)는 만들지 않기로 결정했다
# (services/calendar.py의 ingest_fomc_year 주석 참고).
#
# 아직 의사록 공개일이 연준 공식 캘린더에 게시되지 않은 회의(9/10/12월)는 MINUTES 이벤트를
# 만들지 않는다 - 공개일이 게시되면 core/fed_client.py의 해당 항목에 날짜를 채우고 이 스크립트를
# 다시 실행해야 한다.
#
# 실행: backend/ 디렉토리에서 `uv run python scripts/seed_fomc_2026.py`
# 전제: calendar_events 테이블이 Supabase에 이미 생성되어 있어야 한다.

import asyncio

from backend.domain.calendar.services import calendar as calendar_service


async def main() -> None:
    events = await calendar_service.ingest_fomc_year(2026)
    print(f"=== FOMC 2026년: {len(events)}건 upsert ===")
    for event in events:
        print(
            f"  {event.id} | publishedAt={event.publishedAt} time={event.time} "
            f"| category={event.category} status={event.status}"
        )


if __name__ == "__main__":
    asyncio.run(main())
