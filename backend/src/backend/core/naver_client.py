# naver_client.py
# 네이버 뉴스 검색 API 직접 호출
#
# 네이버 클라우드 플랫폼(NCP)의 NAVER API HUB를 통해 호출한다.
# developers.naver.com 쪽 검색 API와는 주소·헤더가 다르니 주의 (키도 서로 호환되지 않음).
# 하루 25,000회 호출 한도.

import time

import httpx

from backend.core.config import get_settings

_NEWS_ENDPOINT = "https://naverapihub.apigw.ntruss.com/search/v1/news"

# 조회 실패 시 재시도 설정
_RETRY_COUNT = 3
_RETRY_WAIT_SECONDS = 0.5
_TIMEOUT_SECONDS = 10.0


# 뉴스 검색
# query: 검색어 (예: "코스피", "삼성전자") - 필수값이다. 이 API는 "오늘 주요 뉴스"를 그냥 주지 않는다
# display: 가져올 기사 수 (1~100)
# sort: "sim"(정확도순) 또는 "date"(최신순)
#   기본값을 sim으로 둔 이유: date는 관련도를 거의 안 봐서 검색어와 상관없는 최신 기사가 올라온다
#   ('시간외 거래'로 검색하면 게임 기사가 나오는 식 - 실제 호출로 확인)
#
# 응답 items의 각 항목: title / originallink / link / description / pubDate
#   - title과 description에는 검색어가 <b> 태그로 감싸져 오므로 화면에 쓰기 전 제거가 필요하다
#   - link는 네이버 제휴 기사면 n.news.naver.com 주소, 아니면 언론사 원문 주소가 온다
#   - originallink는 항상 언론사 원문 주소다
#
# 일시적인 실패(5xx, 타임아웃)는 여기서 다시 시도한다
# 4xx는 요청이나 키가 잘못된 것이라 다시 보내도 결과가 같으므로 바로 에러를 낸다
def search_news(query: str, display: int = 10, sort: str = "sim") -> dict:
    settings = get_settings()
    if not settings.naver_api_key_id or not settings.naver_api_key:
        raise RuntimeError("NAVER_API_KEY_ID / NAVER_API_KEY가 .env에 없습니다. backend/.env에 추가해주세요.")

    last_error = None
    for attempt in range(_RETRY_COUNT):
        try:
            response = httpx.get(
                _NEWS_ENDPOINT,
                headers={
                    "X-NCP-APIGW-API-KEY-ID": settings.naver_api_key_id,
                    "X-NCP-APIGW-API-KEY": settings.naver_api_key,
                },
                params={"query": query, "display": display, "sort": sort},
                timeout=_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as error:
            if error.response.status_code < 500:
                raise
            last_error = error
        except httpx.TransportError as error:
            last_error = error

        if attempt < _RETRY_COUNT - 1:
            time.sleep(_RETRY_WAIT_SECONDS * (attempt + 1))

    raise last_error
