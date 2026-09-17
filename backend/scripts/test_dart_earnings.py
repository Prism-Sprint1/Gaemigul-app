# test_dart_earnings.py
#
# DART 잠정실적 공시를 calendar_events에 earnings 이벤트로 저장하는 테스트. 삼성전자/
# SK하이닉스/현대차 3개 기업을 대상으로 한다(2025~2026년). 실제로 DB에 쓰기 전에 먼저 조회
# 결과만 출력해서 확인하고, 그 다음에만 저장 로직(ingest_preliminary_earnings_from_dart)을
# 실행한다. corp_code는 추측하지 않고 dart_client.get_corp_codes() +
# find_corp_by_stock_code()로 직접 조회해서 확인한 값이다(아래 COMPANIES 참고).
#
# 미국 기업(NVIDIA/Apple)은 이번 단계에 포함하지 않는다 - 다음 단계에서 별도 데이터 소스로 처리.
#
# 실행: backend/ 디렉토리에서 `uv run python scripts/test_dart_earnings.py`
# 전제: calendar_events 테이블이 Supabase에 이미 생성되어 있어야 한다.

import asyncio

from backend.core import dart_client
from backend.domain.calendar.services import calendar as calendar_service

# corp_code는 get_corp_codes()+find_corp_by_stock_code()로 실제 조회해서 확인한 값이다
# (추측 금지 - 조회 방법은 scripts/test_dart_samsung.py 참고). corp_name은 DART 등록명이
# 아니라 캘린더에 표시할 이름을 쓴다(현대자동차의 DART 등록명은 "현대자동차"이지만 캘린더에는
# "현대차"로 표시한다).
COMPANIES = [
    {"corp_code": "00126380", "corp_name": "삼성전자", "stock_code": "005930"},
    {"corp_code": "00164779", "corp_name": "SK하이닉스", "stock_code": "000660"},
    {"corp_code": "00164742", "corp_name": "현대차", "stock_code": "005380"},
]

SEARCH_BGN_DE = "20250101"
SEARCH_END_DE = "20260915"


async def main() -> None:
    print("=== 1. 미리보기 — 기업별 1차 잠정실적 공시만 조회 (DB 저장 없음) ===")
    preview: dict[str, list[dict]] = {}
    for company in COMPANIES:
        disclosures = dart_client.get_preliminary_earnings(
            company["corp_code"], SEARCH_BGN_DE, SEARCH_END_DE
        )
        preview[company["corp_code"]] = disclosures
        print(f"\n[{company['corp_name']}] corp_code={company['corp_code']} "
              f"stock_code={company['stock_code']} - 1차 잠정실적 {len(disclosures)}건")
        for d in disclosures:
            bsns_year, reprt_code, period_label = calendar_service._dart_quarter_period(d["rcept_dt"])
            accounts = dart_client.get_key_accounts(company["corp_code"], bsns_year, reprt_code)
            print(
                f"  rcept_dt={d['rcept_dt']} period={period_label} report_nm={d['report_nm'].strip()} "
                f"매출액={accounts['revenue']} 영업이익={accounts['operating_income']} "
                f"당기순이익={accounts['net_income']}"
            )

    print("\n검증 결과가 맞다고 판단해서 저장을 진행합니다.\n")

    print("=== 2. calendar_events 저장 (1차 실행) ===")
    all_events = []
    for company in COMPANIES:
        events = await calendar_service.ingest_preliminary_earnings_from_dart(
            company["corp_code"],
            company["stock_code"],
            company["corp_name"],
            SEARCH_BGN_DE,
            SEARCH_END_DE,
        )
        all_events.extend(events)
        print(f"\n[{company['corp_name']}] {len(events)}건 upsert")
        for e in events:
            print(
                f"  {e.id} | publishedAt={e.publishedAt} category={e.category} "
                f"actual={e.actual} status={e.status}"
            )
            print(f"    summary: {e.summary}")

    print(f"\n전체 {len(all_events)}건 upsert 완료")

    print("\n=== 3. 중복 방지 확인 — 같은 함수 재실행 (2차 실행) ===")
    total_again = 0
    for company in COMPANIES:
        events_again = await calendar_service.ingest_preliminary_earnings_from_dart(
            company["corp_code"],
            company["stock_code"],
            company["corp_name"],
            SEARCH_BGN_DE,
            SEARCH_END_DE,
        )
        total_again += len(events_again)
    print(f"재실행 결과도 동일하게 {total_again}건 (upsert라 중복 생성되지 않아야 함)")


if __name__ == "__main__":
    asyncio.run(main())
