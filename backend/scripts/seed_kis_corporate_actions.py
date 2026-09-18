# seed_kis_corporate_actions.py
# 한국투자증권(KIS)에서 2026년 신규상장(IPO) 일정을 가져와서 Supabase calendar_events에 upsert한다.
#
# 유상증자/무상증자는 사용자 결정으로 캘린더에서 제외했다(IMPLEMENTATION_LOG.md 26번 항목) -
# 초보 투자자에게 IPO만큼 중요하지 않고, 유상증자만 82건이라 넣으면 낯선 중소형주 이름으로
# 캘린더가 채워져 정작 중요한 지표/배당이 묻힐 수 있다는 판단. 기존에 넣었던 83건(유상증자 82 +
# 무상증자 1)은 Supabase에서 직접 삭제했다. 관련 함수(`ingest_paidin_capital_increases_from_kis`,
# `ingest_bonus_issues_from_kis`)는 services/calendar.py에 남겨뒀다 - 나중에 다시 필요해지면
# 이 스크립트에 호출만 추가하면 된다.
#
# 실행: backend/ 디렉토리에서 `uv run python scripts/seed_kis_corporate_actions.py`
# 전제: calendar_events 테이블이 Supabase에 이미 생성되어 있어야 한다.

import asyncio

from backend.domain.calendar.services import calendar as calendar_service


async def main() -> None:
    ipos = await calendar_service.ingest_ipos_from_kis("20260101", "20261231")
    print(f"=== 신규상장(IPO): {len(ipos)}건 upsert ===")
    for event in ipos:
        print(f"  {event.id} | publishedAt={event.publishedAt} | actual={event.actual} status={event.status} | {event.title}")


if __name__ == "__main__":
    asyncio.run(main())
