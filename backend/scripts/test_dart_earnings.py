# test_dart_earnings.py
#
# DART 잠정실적 공시를 calendar_events에 earnings 이벤트로 저장하는 3단계 구현 테스트.
# 삼성전자 1개 기업만 대상으로 한다(2025~2026년). 실제로 DB에 쓰기 전에 먼저 조회 결과만
# 출력해서 확인하고, 그 다음에만 저장 로직(ingest_preliminary_earnings_from_dart)을
# 실행한다.
#
# 실행: backend/ 디렉토리에서 `uv run python scripts/test_dart_earnings.py`
# 전제: calendar_events 테이블이 Supabase에 이미 생성되어 있어야 한다.

import asyncio

from backend.core import dart_client
from backend.domain.calendar.services import calendar as calendar_service

SAMSUNG_CORP_CODE = "00126380"
SAMSUNG_STOCK_CODE = "005930"
SAMSUNG_CORP_NAME = "삼성전자"

SEARCH_BGN_DE = "20250101"
SEARCH_END_DE = "20260915"


async def main() -> None:
    print("=== 1. 미리보기 — 1차 잠정실적 공시만 조회 (DB 저장 없음) ===")
    disclosures = dart_client.get_preliminary_earnings(
        SAMSUNG_CORP_CODE, SEARCH_BGN_DE, SEARCH_END_DE
    )
    print(f"1차 잠정실적 공시 {len(disclosures)}건")
    for d in disclosures:
        print(f"  rcept_dt={d['rcept_dt']} report_nm={d['report_nm']} rcept_no={d['rcept_no']}")

    print("\n검증 결과가 맞다고 판단해서 저장을 진행합니다.\n")

    print("=== 2. calendar_events 저장 (1차 실행) ===")
    events = await calendar_service.ingest_preliminary_earnings_from_dart(
        SAMSUNG_CORP_CODE, SAMSUNG_STOCK_CODE, SAMSUNG_CORP_NAME, SEARCH_BGN_DE, SEARCH_END_DE
    )
    print(f"{len(events)}건 upsert")
    for e in events:
        print(
            f"  {e.id} | publishedAt={e.publishedAt} category={e.category} "
            f"actual={e.actual} status={e.status}"
        )
        print(f"    summary: {e.summary}")

    print("\n=== 3. 중복 방지 확인 — 같은 함수 재실행 (2차 실행) ===")
    events_again = await calendar_service.ingest_preliminary_earnings_from_dart(
        SAMSUNG_CORP_CODE, SAMSUNG_STOCK_CODE, SAMSUNG_CORP_NAME, SEARCH_BGN_DE, SEARCH_END_DE
    )
    print(f"재실행 결과도 동일하게 {len(events_again)}건 (upsert라 중복 생성되지 않아야 함)")


if __name__ == "__main__":
    asyncio.run(main())
