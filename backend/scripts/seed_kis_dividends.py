# seed_kis_dividends.py
# 한국투자증권(KIS) 예탁원정보(배당일정)에서 주요 국내 기업의 2026년 배당 일정을 가져와서
# Supabase calendar_events에 upsert한다. 전체 종목 조회는 페이지당 100건 제한이 있어서,
# 종목코드를 하나씩 지정해서 조회하는 방식을 쓴다(services/calendar.py의
# ingest_dividends_from_kis 참고).
#
# 실행: backend/ 디렉토리에서 `uv run python scripts/seed_kis_dividends.py`
# 전제: calendar_events 테이블이 Supabase에 이미 생성되어 있어야 한다.

import asyncio

from backend.domain.calendar.services import calendar as calendar_service

# 시가총액 상위 위주 코스피 주요 기업 29개 (종목코드: 종목명)
MAJOR_STOCKS: dict[str, str] = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "373220": "LG에너지솔루션",
    "207940": "삼성바이오로직스",
    "005380": "현대차",
    "000270": "기아",
    "068270": "셀트리온",
    "105560": "KB금융",
    "055550": "신한지주",
    "005490": "POSCO홀딩스",
    "035420": "NAVER",
    "006400": "삼성SDI",
    "051910": "LG화학",
    "012450": "한화에어로스페이스",
    "329180": "HD현대중공업",
    "028260": "삼성물산",
    "086790": "하나금융지주",
    "138040": "메리츠금융지주",
    "096770": "SK이노베이션",
    "035720": "카카오",
    "034730": "SK",
    "066570": "LG전자",
    "316140": "우리금융지주",
    "012330": "현대모비스",
    "032830": "삼성생명",
    "259960": "크래프톤",
    "009540": "HD한국조선해양",
    "015760": "한국전력",
    "010950": "S-Oil",
}


async def main() -> None:
    events = await calendar_service.ingest_dividends_from_kis(
        list(MAJOR_STOCKS.keys()), "20260101", "20261231"
    )
    print(f"=== KIS 배당일정 {len(MAJOR_STOCKS)}개 종목 조회, {len(events)}건 upsert ===")
    for event in events:
        print(
            f"  {event.id} | publishedAt={event.publishedAt} "
            f"| actual={event.actual} status={event.status} | {event.title}"
        )


if __name__ == "__main__":
    asyncio.run(main())
