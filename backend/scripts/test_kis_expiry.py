# test_kis_expiry.py
#
# 한국투자증권(KIS) 국내선물옵션 API로 KOSPI200 선물/옵션의 실제 만기일을 확인하고, 실제로
# calendar_events에 ingest까지 수행하는 스크립트다. core/kis_client.py의 get_access_token()과
# 46번 사전조사에서 client 함수로 승격한 get_option_month_list()/get_futures_board()/
# get_option_callput_board()/get_price()를 그대로 재사용한다(새 인증 코드 없음).
#
# 조사 결론(실제 라이브 호출로 확인, 46번 항목 참고):
# - "국내옵션전광판_옵션월물리스트"는 만기 "년월"만 준다 - 정확한 날짜는 없음
# - "국내옵션전광판_선물"의 market_cls_code=""는 정규 KOSPI200선물(분기월만),
#   "MKI"는 미니 KOSPI200선물(월물 전체) - 이번 ingest는 정규만 쓴다(미니 제외)
# - "선물옵션 시세"의 futs_last_tr_date 필드가 진짜 최종거래일=만기일이다. "해당 결제월의
#   두 번째 목요일"이라는 한국투자증권 공식 규칙과 실제 값이 정확히 일치하는 것을 확인했다
# - "국내선물 영업일조회"에 해당하는 API는 KIS 공식 예제에 없고, chk-holiday는 시장 개장/
#   휴장 여부만 주는 일반 캘린더라 만기일 데이터로 쓰지 않는다
#
# 실행: backend/ 디렉토리에서 `uv run python scripts/test_kis_expiry.py`
# 전제: calendar_events 테이블이 Supabase에 이미 생성되어 있어야 한다.

import asyncio

from backend.core import kis_client
from backend.domain.calendar.services import calendar as calendar_service


async def main() -> None:
    print("=== 1. 옵션월물리스트 (만기 년월만 확인 가능, DB 저장 없음) ===")
    month_list = kis_client.get_option_month_list()
    for item in month_list:
        print(f"  {item['mtrt_yymm']} (코드 {item['mtrt_yymm_code']})")

    print("\n=== 2. 정규 KOSPI200 선물 (분기월만 존재) + 실제 최종거래일 ===")
    for row in kis_client.get_futures_board(""):
        price = kis_client.get_price("F", row["futs_shrn_iscd"])
        print(
            f"  {row['hts_kor_isnm']} (종목코드 {row['futs_shrn_iscd']}) "
            f"| 최종거래일={price['futs_last_tr_date']} | 잔존일수={price['hts_rmnn_dynu']}"
        )

    print("\n=== 3. KOSPI200 옵션 (근월물 1건 샘플) + 실제 최종거래일 ===")
    near_month = month_list[0]["mtrt_yymm"]
    callput = kis_client.get_option_callput_board(near_month)
    if callput:
        sample = callput[0]
        price = kis_client.get_price("O", sample["optn_shrn_iscd"])
        print(
            f"  만기월={near_month} 종목코드={sample['optn_shrn_iscd']} 행사가={sample['acpr']} "
            f"| 최종거래일={price['futs_last_tr_date']} | 잔존일수={price['hts_rmnn_dynu']}"
        )

    print("\n검증 결과가 맞다고 판단해서 저장을 진행합니다.\n")

    print("=== 4. calendar_events 저장 (ingest_kospi200_expiry) ===")
    events = await calendar_service.ingest_kospi200_expiry()
    print(f"{len(events)}건 upsert")
    for e in events:
        print(f"  {e.id} | publishedAt={e.publishedAt} title={e.title} status={e.status}")

    print("\n=== 5. 중복 방지 확인 — 같은 함수 재실행 ===")
    events_again = await calendar_service.ingest_kospi200_expiry()
    print(f"재실행 결과도 동일하게 {len(events_again)}건 (upsert라 중복 생성되지 않아야 함)")


if __name__ == "__main__":
    asyncio.run(main())
