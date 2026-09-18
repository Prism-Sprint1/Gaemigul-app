# test_rate_api.py
#
# 한국은행 ECOS(경제통계시스템) Open API로 "한국은행 기준금리"(통계표코드 722Y001, 통계항목코드
# 0101000)를 조회해서 확인한 뒤, 실제로 calendar_events에 ingest까지 수행하는 스크립트다.
#
# 중요: ECOS는 "레벨 값이 매달 얼마였는지"만 주는 통계 DB라서, 그 값이 그대로 유지되는 달에도
# 매달 행이 반복해서 나온다(예: 3.5, 3.5, 3.5, ...). "몇 월에 결정됐는지"는 이 API 응답만으로는
# 알 수 없고, 값이 바뀌는 지점(=금통위가 실제로 금리를 조정한 달)만 골라내야 한다. 심지어 그
# "달"도 정확한 "결정일"은 아니다 - 정확한 결정일은 한국은행 공식 홈페이지에서만 확인할 수
# 있어서, services/calendar.py의 _BOK_RATE_DECISION_DATES(정적 표, fed_client.py와 같은
# 성격)에 옮겨뒀다. ingest_bok_rate_decisions()는 이 표에 매핑이 있는 변경월만 이벤트로 만든다.
#
# 실행: backend/ 디렉토리에서 `uv run python scripts/test_rate_api.py`
# 전제: backend/.env에 ECOS_API_KEY가 있으면 그 키로, 없으면 "sample" 키로 호출한다
#       ("sample"은 실제 데이터가 나오지만 한 번에 최대 10건까지만 조회 가능).

import asyncio

from backend.core import ecos_client
from backend.core.config import get_settings
from backend.domain.calendar.services import calendar as calendar_service

_SEARCH_START = "202401"
_SEARCH_END = "202609"


async def main() -> None:
    settings = get_settings()
    print(f"=== 1. ECOS get_base_rate_series() 조회 (키: {'실제 키' if settings.ecos_api_key else 'sample'}) ===")

    rows = ecos_client.get_base_rate_series(_SEARCH_START, _SEARCH_END)
    print(f"총 {len(rows)}개월 데이터 조회됨")
    print(f"통계표명: {rows[0]['STAT_NAME']} / 항목명: {rows[0]['ITEM_NAME1']} / 단위: {rows[0]['UNIT_NAME']}")

    print("\n=== 2. 값이 바뀐 달만 (실제 금리 조정이 있었던 달) ===")
    prev_value: str | None = None
    for row in rows:
        value = row["DATA_VALUE"]
        if prev_value is not None and value != prev_value:
            print(f"  {row['TIME']}: {prev_value} -> {value}")
        prev_value = value

    print("\n검증 결과가 맞다고 판단해서 저장을 진행합니다.\n")

    print("=== 3. calendar_events 저장 (ingest_bok_rate_decisions) ===")
    events = await calendar_service.ingest_bok_rate_decisions(_SEARCH_START, _SEARCH_END)
    print(f"{len(events)}건 upsert")
    for e in events:
        print(f"  {e.id} | publishedAt={e.publishedAt} previous={e.previous} actual={e.actual} status={e.status}")

    print("\n=== 4. 중복 방지 확인 — 같은 함수 재실행 ===")
    events_again = await calendar_service.ingest_bok_rate_decisions(_SEARCH_START, _SEARCH_END)
    print(f"재실행 결과도 동일하게 {len(events_again)}건 (upsert라 중복 생성되지 않아야 함)")


if __name__ == "__main__":
    asyncio.run(main())
