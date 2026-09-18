# seed_kospi100_earnings.py
# 코스피 시가총액 상위 100개 기업의 DART 잠정실적(2024 Q4~2026 Q2 범위)을 calendar_events에
# 백필한다. 이미 구현된 삼성전자/SK하이닉스/현대차 DART 잠정실적 파이프라인
# (services/calendar.py의 ingest_preliminary_earnings_from_dart)을 기업 수만 100개로
# 넓혀서 그대로 재사용한다 - 이 함수/그 안의 _dart_earnings_event, _upsert_event(ON CONFLICT
# 로 중복 방지)는 전혀 수정하지 않았다.
#
# 기업 목록 선정 기준: kis_client.get_stock_master("kospi")(코스피 보통주 전종목, KIS 공식
# 종목마스터파일 기준 market_cap 포함)를 시가총액 내림차순 정렬한 뒤 상위 100개
# (services/calendar.py의 get_kospi_top100_companies) - 실행 시점 스냅샷이라 기준일은
# 이 스크립트를 실행한 시각이다.
#
# 실행: backend/ 디렉토리에서 `uv run python scripts/seed_kospi100_earnings.py`
# 전제: calendar_events 테이블이 Supabase에 이미 생성되어 있어야 한다.

import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import text

from backend.core.database import async_session
from backend.domain.calendar.services import calendar as calendar_service

_KST = ZoneInfo("Asia/Seoul")
# 2024 Q4 1차 공시(삼성전자 실측 기준 2025-01-08)를 포함하기 위해 이보다 이르게 잡는다.
_START_DATE = "20250101"


async def _existing_earnings_ids() -> set[str]:
    async with async_session() as session:
        result = await session.execute(text("SELECT id FROM calendar_events WHERE category = 'earnings'"))
        return {row[0] for row in result.all()}


async def main() -> None:
    end_date = datetime.now(_KST).strftime("%Y%m%d")

    companies = calendar_service.get_kospi_top100_companies()
    mapped, unmapped = calendar_service.map_dart_corp_codes(companies)

    before_ids = await _existing_earnings_ids()

    succeeded: list[tuple[str, int]] = []
    no_disclosure: list[str] = []
    failed: list[tuple[str, str]] = []
    attempted_ids: set[str] = set()
    per_company_ids: dict[str, set[str]] = {}

    for company in mapped:
        try:
            events = await calendar_service.ingest_preliminary_earnings_from_dart(
                company["corp_code"],
                company["stock_code"],
                company["corp_name"],
                _START_DATE,
                end_date,
            )
        except Exception as exc:  # noqa: BLE001 - main.py의 _refresh_dart_earnings와 동일하게 기업 단위로 격리
            failed.append((company["corp_name"], f"{type(exc).__name__}: {exc}"))
            continue

        ids = {event.id for event in events}
        attempted_ids |= ids
        per_company_ids[company["corp_name"]] = ids
        if events:
            succeeded.append((company["corp_name"], len(events)))
        else:
            no_disclosure.append(company["corp_name"])

    new_ids = attempted_ids - before_ids
    duplicate_ids = attempted_ids & before_ids

    # 분기 라벨(예: "2026년 2분기")별 집계 - _dart_quarter_period가 이미 검증된 월->분기 매핑을
    # 갖고 있어 그대로 재사용(발표월이 1/4/7/10월이 아니면 여기서도 건너뛴다).
    quarter_counts: dict[str, int] = {}
    for ids in per_company_ids.values():
        for event_id in ids:
            rcept_dt = event_id.rsplit("-", 1)[-1]
            try:
                _, _, quarter_label = calendar_service._dart_quarter_period(rcept_dt)
            except ValueError:
                quarter_label = f"확인 필요({rcept_dt})"
            quarter_counts[quarter_label] = quarter_counts.get(quarter_label, 0) + 1

    async with async_session() as session:
        category_check = await session.execute(
            text("SELECT DISTINCT category FROM calendar_events WHERE id = ANY(:ids)"),
            {"ids": list(attempted_ids)},
        )
        categories = {row[0] for row in category_check.all()}

    print("=== 대상 기업 ===")
    print(f"코스피 시총 상위 100개 중 대상: {len(companies)}건")
    print(f"DART corp_code 매핑 성공: {len(mapped)}건 / 실패: {len(unmapped)}건")
    if unmapped:
        for company in unmapped:
            print(f"  - 매핑 실패: {company['corp_name']}({company['stock_code']})")

    print("\n=== 실적 공시 수집 결과 ===")
    print(f"잠정실적 공시가 확인된 기업: {len(succeeded)}건")
    print(f"공시가 없었던 기업(정상, 오류 아님): {len(no_disclosure)}건")
    print(f"수집 중 오류로 실패한 기업: {len(failed)}건")
    for corp_name, error in failed:
        print(f"  - 실패: {corp_name} - {error}")

    print("\n=== calendar_events 저장 결과 ===")
    print(f"이번 실행에서 시도한 이벤트 id 총합: {len(attempted_ids)}건")
    print(f"신규 저장: {len(new_ids)}건")
    print(f"기존 데이터와 동일 id(중복 방지, upsert로 재확인만 됨): {len(duplicate_ids)}건")
    print(f"category 전부 'earnings'인지: {categories == {'earnings'} if attempted_ids else '해당 없음'} ({categories})")

    print("\n=== 분기별 집계 ===")
    for label, count in sorted(quarter_counts.items()):
        print(f"  {label}: {count}건")

    print("\n=== 기업별 저장 이벤트 수 (상위 10개만 표시) ===")
    for corp_name, count in sorted(succeeded, key=lambda x: -x[1])[:10]:
        print(f"  {corp_name}: {count}건")


if __name__ == "__main__":
    asyncio.run(main())
