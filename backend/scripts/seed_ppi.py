# seed_ppi.py
# FRED PPI(PPIACO)를 1회 가져와서 Supabase calendar_events에 저장하는 수동 스크립트.
# main.py 스케줄러에는 아직 연결하지 않는다 - 기본 흐름이 정상 동작한 뒤 별도로 자동화할 예정.
#
# 실행: backend/ 디렉토리에서 `uv run python scripts/seed_ppi.py`
# 전제: calendar_events 테이블이 Supabase에 이미 생성되어 있어야 한다.

import asyncio

from backend.domain.calendar.services import calendar as calendar_service


async def main() -> None:
    event = await calendar_service.ingest_ppi_from_fred()
    print(
        f"저장 완료: {event.id} | publishedAt={event.publishedAt} time={event.time} "
        f"| actual={event.actual} previous={event.previous} status={event.status}"
    )


if __name__ == "__main__":
    asyncio.run(main())
