# seed_2026_calendar.py
# FRED CPI/PPI/GDP/PAYEMS/UNRATE/PCE 2026년 데이터를 한 번에 가져와서 Supabase calendar_events에
# upsert한다. CPI/PPI/PAYEMS/UNRATE/PCE는 월별(1~12월), GDP는 분기별(1/4/7/10월)로 자동 처리된다
# (services/calendar.py의 _FREQUENCY 표 기준). PCE는 GDP와 발표일 캘린더를 공유하므로(같은 BEA
# release 계열) ingest_year_from_fred()의 실측 검증 로직(realtime 고정 조회)이 특히 중요하다.
# 이미 발표된 기간은 RELEASED+실제값, FRED release calendar에 예정 발표일이 확인되는 아직 발표
# 안 된 기간은 SCHEDULED(actual=null)로 저장한다. 예정 발표일 자체가 없는 기간은 만들지 않는다.
#
# FEDFUNDS(연방기금금리)는 여기 포함하지 않는다 - H.15 통계는 매 영업일 발행돼서 "발표 이벤트"
# 개념 자체가 CPI/PPI 등과 다르다(IMPLEMENTATION_LOG.md 18번 항목 참고).
#
# 실행: backend/ 디렉토리에서 `uv run python scripts/seed_2026_calendar.py`
# 전제: calendar_events 테이블이 Supabase에 이미 생성되어 있어야 한다.

import asyncio

from backend.domain.calendar.services import calendar as calendar_service


async def main() -> None:
    for indicator in ("CPI", "PPI", "GDP", "PAYEMS", "UNRATE", "PCE"):
        events = await calendar_service.ingest_year_from_fred(indicator, 2026)
        print(f"=== {indicator} 2026년: {len(events)}건 upsert ===")
        for event in events:
            print(
                f"  {event.id} | publishedAt={event.publishedAt} time={event.time} "
                f"| actual={event.actual} previous={event.previous} status={event.status}"
            )


if __name__ == "__main__":
    asyncio.run(main())
