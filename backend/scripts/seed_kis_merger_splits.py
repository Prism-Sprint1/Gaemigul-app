# seed_kis_merger_splits.py
#
# ⚠️ 사용자 결정으로 합병/분할은 캘린더에서 제외했다(IMPLEMENTATION_LOG.md 27번 항목) - 보유
# 종목이 아닌 이상 초보 투자자가 능동적으로 찾아볼 정보가 아니라는 판단. 이전에 upsert했던 30건은
# Supabase에서 직접 삭제했다. 이 스크립트를 다시 실행하면 그 30건이 재생성되니, 정책이 다시
# 바뀌기 전에는 실행하지 말 것.
#
# 한국투자증권(KIS) 예탁원정보(합병_분할일정)에서 2026년 전체 시장의 합병/분할 일정을 가져와서
# Supabase calendar_events에 upsert한다. 연간 건수가 적어(30건 안팎) 종목코드 없이 전체 조회
# 한 번으로 충분하다(services/calendar.py의 ingest_merger_splits_from_kis 참고).
#
# 실행: backend/ 디렉토리에서 `uv run python scripts/seed_kis_merger_splits.py`
# 전제: calendar_events 테이블이 Supabase에 이미 생성되어 있어야 한다.

import asyncio

from backend.domain.calendar.services import calendar as calendar_service


async def main() -> None:
    events = await calendar_service.ingest_merger_splits_from_kis("20260101", "20261231")
    print(f"=== KIS 합병/분할일정: {len(events)}건 upsert ===")
    for event in events:
        print(
            f"  {event.id} | publishedAt={event.publishedAt} "
            f"start_date={event.start_date} end_date={event.end_date} "
            f"| actual={event.actual} status={event.status} | {event.title}"
        )


if __name__ == "__main__":
    asyncio.run(main())
