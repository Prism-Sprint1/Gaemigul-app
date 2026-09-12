# news_service.py
# 네이버 뉴스 검색 결과를 타임라인 슬롯에 넣을 형태로 정제한다
#
# 검색 방식에 대해 알아둘 것:
#   네이버 뉴스 API는 "이 시간대 주요 뉴스"를 주지 않는다. 검색어를 넣어야만 그에 맞는 기사를 준다.
#   그래서 슬롯마다 쓸 검색어를 아래 _SLOT_KEYWORDS에 정해뒀다.
#
#   정렬은 반드시 "sim"(정확도순)을 쓴다. "date"(최신순)는 관련도를 거의 안 보기 때문에
#   '시간외 거래'로 검색하면 게임 기사가 나오는 식으로 엉뚱한 결과가 섞인다(실제 호출로 확인).
#   대신 sim은 며칠 지난 기사도 올라오므로, 받아온 뒤 슬롯 구간에 드는 기사만 남기고
#   중요도 점수순으로 고른다.

import html
import logging
import re

import httpx
from datetime import date, datetime, time, timedelta
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

from backend.core import llm_client, naver_client
from backend.domain.timeline.services import prompts

_KST = ZoneInfo("Asia/Seoul")

logger = logging.getLogger(__name__)

# 슬롯별 검색어. 이 표만 고치면 어느 시간대에 어떤 기사를 모을지 바뀐다
#
# 각 슬롯의 관심사가 달라서 검색어를 나눴다. 예를 들어 07:30은 밤사이 미국장이 궁금한 시간인데
# "코스피"로 검색하면 어제 국내장 기사가 올라온다.
#
# 검색어를 고를 때의 경향(실제로 돌려보고 정리한 것):
#   - 단어가 짧고 하나일수록 잘 맞는다. 두 단어 이상이면 부분 매칭으로 엉뚱한 기사가 섞인다
#   - "개장시황", "마감시황"처럼 기사 제목에 실제로 쓰이는 말머리가 정확도가 높다
#   - "환율"처럼 일상어이기도 한 단어는 엉뚱한 기사를 물어온다("애플식 환율" 같은 제품 가격 기사).
#     "원달러 환율"로 좁히면 외환시장 기사만 나온다
#   - "프리마켓", "애프터마켓", "시간외"는 시황 기사가 아니라 제도 소개 기사만 나와서 뺐다.
#     한국거래소 애프터마켓(오후 4~8시)이 자리잡으면 17:30 슬롯에서 다시 시험해볼 것
#   - "개장 전"은 야영장 개장, 터미널 개장 같은 기사가 나와서 뺐다. 증시 용어로 안 쓰이는 말이다
_SLOT_KEYWORDS = {
    "07:30": ["뉴욕증시", "미국 증시", "나스닥", "국제유가", "미국 국채금리", "원달러 환율"],
    "08:30": ["증시 전망", "코스피 개장", "글로벌 증시", "원달러 환율", "국제유가"],
    "09:30": ["개장시황", "코스피", "코스닥", "특징주", "외국인 순매수"],
    "12:00": ["장중시황", "코스피", "코스닥", "특징주", "외국인 순매수"],
    "14:00": ["장중시황", "코스피", "코스닥", "특징주", "기관 순매수"],
    "15:30": ["마감시황", "코스피", "코스닥", "특징주", "증시 마감"],
    "17:30": ["마감시황", "코스피", "코스닥", "특징주", "증시 마감"],
    "20:00": ["증시 전망", "시황", "내일 증시", "코스피", "글로벌 증시"],
}

# 검색어 하나당 가져올 기사 수. sim 정렬이라 넉넉히 받아서 걸러내는 편이 좋다
_FETCH_PER_KEYWORD_DEFAULT = 30
_FETCH_PER_KEYWORD = {"07:30": 50}

# 슬롯별 뉴스 수집 구간. (구간 시작 시각, 시작이 전날인지)
#
# 각 슬롯은 "직전 슬롯 이후에 새로 나온 기사"만 담는다. 그래야 타임라인을 내려볼 때 시간 순서대로
# 새 소식이 이어진다. 예전에는 모든 슬롯이 "최근 24시간"이었는데, 그러면 09:30과 12:00 슬롯이
# 10건 중 9건 같은 기사를 보여줬다(실제 측정값).
#
# 07:30만 전날 20:00부터 잡는다. 밤사이 해외장 기사를 담아야 하기 때문이다.
#
# 구간은 [시작, 끝) - 시작은 포함, 끝은 배타다. 네이버 pubDate가 분 단위라서(표본 400건 전부
# 초가 00) 실제로는 아래와 같이 잘린다. 빈틈도 겹침도 없다.
#
#   07:30 슬롯   전날 20:00 ~ 07:29      08:30 슬롯   07:30 ~ 08:29
#   09:30 슬롯   08:30 ~ 09:29           12:00 슬롯   09:30 ~ 11:59
#   14:00 슬롯   12:00 ~ 13:59           15:30 슬롯   14:00 ~ 15:29
#   17:30 슬롯   15:30 ~ 17:29           20:00 슬롯   17:30 ~ 19:59
#
# 구간을 바꾸려면 이 표만 고치면 된다
_SLOT_WINDOW = {
    "07:30": ("20:00", True),
    "08:30": ("07:30", False),
    "09:30": ("08:30", False),
    "12:00": ("09:30", False),
    "14:00": ("12:00", False),
    "15:30": ("14:00", False),
    "17:30": ("15:30", False),
    "20:00": ("17:30", False),
}

# 구간 안에 기사가 이만큼도 없으면 구간을 넓혀서 다시 거른다
# 08:30 슬롯처럼 구간이 1시간밖에 안 되는 경우 기사가 거의 없을 수 있어서 넣은 장치다
_MIN_ITEMS = 3
_FALLBACK_HOURS = 6

# 중요도 점수를 낼 때 쓰는 값
#
# 검색어마다 네이버가 정확도순으로 기사를 주는데, 그 순위를 1/(_RANK_BIAS + 순위)로 바꿔서 더한다.
# 이렇게 하면 두 가지가 자연스럽게 반영된다.
#   1. 여러 검색어에 동시에 걸린 기사일수록 점수가 높아진다 - 여러 각도에서 잡히는 기사가 중심 뉴스다
#   2. 각 검색어 안에서 위에 있을수록 점수가 높아진다
#
# _RANK_BIAS를 키우면 순위 간 점수 차이가 줄어서 "여러 검색어에 걸렸는지"가 더 중요해지고,
# 줄이면 "1등이었는지"가 더 중요해진다. 60은 이런 방식에서 흔히 쓰는 기본값이다
_RANK_BIAS = 60

# LLM에게 넘길 후보 기사 수
# 많이 넘길수록 고를 폭은 넓어지지만 프롬프트가 길어지고 LLM이 번호를 헷갈릴 확률이 올라간다
#
# 07:30만 두 배로 잡았다. 이 슬롯은 구간이 11시간이 넘어서(전날 20:00부터) 밤사이 쌓인 기사가
# 다른 슬롯의 몇 배다. 30건으로 자르면 새벽에 나온 중요한 기사가 후보에도 못 든다
_CANDIDATE_LIMIT_DEFAULT = 30
_CANDIDATE_LIMITS = {"07:30": 60}

# 한 슬롯에 실을 기사 수의 하한과 상한
# 하한을 둔 이유: 후보가 전부 같은 사건이면 LLM이 중복을 걸러내다가 2건만 남기는 경우가 있는데,
# 화면에 뉴스 카드가 두 장만 뜨면 허전하다. 모자라면 점수 상위 기사로 채운다
#
# 상한을 10에서 8로 줄였다 (2026-09-12). 한 슬롯에 10건이면 스크롤이 길어지는데,
# 하루 8슬롯이면 최대 80건이라 타임라인 전체로 보면 너무 많다.
# 이 값만 고치면 수집·저장·응답에 전부 반영된다(timeline_service._NEWS_LIMIT이 이 값을 쓴다)
_PICK_MIN = 5
_PICK_MAX = 8


# 제목/요약에 섞여 오는 태그와 HTML 특수문자를 없앤다
# 네이버는 검색어를 <b>...</b>로 감싸서 주고, 따옴표는 &quot; 같은 형태로 보낸다 - 화면에 그대로 쓰면 깨진다
def _clean_text(value: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", value)).strip()


# pubDate 문자열을 한국 시간 datetime으로 바꾼다
# 네이버는 "Thu, 10 Sep 2026 11:00:00 +0900" 형식으로 주기 때문에 그냥 datetime으로는 못 읽는다
def _parse_pub_date(value: str) -> datetime:
    return parsedate_to_datetime(value).astimezone(_KST)


# 후보 기사를 LLM에게 넘겨 실을 것만 고른다
#
# LLM에게 기사 내용을 다시 쓰게 하지 않고 번호만 고르게 한다. 제목을 바꿔 쓰거나 요약을 지어낼
# 여지를 없애기 위해서다. 돌려받은 번호로 원본 기사를 그대로 꺼내 쓴다
#
# 실패하면(키가 없거나 응답이 이상하면) 점수 상위 N건으로 넘어간다.
# 뉴스가 아예 안 나오는 것보다 정렬이 덜 정교한 편이 낫기 때문이다
def _select_with_llm(time_slot: str, candidates: list[dict], limit: int) -> list[dict]:
    if not candidates:
        return []

    listed = "\n".join(f"{index}. [{item['published_at']:%m-%d %H:%M}] {item['title']} / {item['summary'][:80]}" for index, item in enumerate(candidates))

    try:
        answer = llm_client.generate_json(
            prompts.NEWS_SELECT_PROMPT.format(
                time_slot=time_slot,
                title=prompts.SLOT_TITLES[time_slot],
                focus=prompts.SLOT_FOCUS[time_slot],
                pick_count=limit,
                min_count=min(_PICK_MIN, len(candidates)),
                candidates=listed,
            )
        )
        # 범위를 벗어난 번호나 중복은 버린다 - LLM이 없는 번호를 답하는 경우가 있다
        seen = set()
        chosen = [index for index in answer.get("selected", []) if isinstance(index, int) and 0 <= index < len(candidates) and not (index in seen or seen.add(index))]
    except (RuntimeError, ValueError, KeyError, httpx.HTTPError) as error:
        logger.warning("뉴스 LLM 선별 실패, 점수순으로 대체합니다 - %s: %s", type(error).__name__, error)
        return candidates[:limit]

    if not chosen:
        logger.warning("뉴스 LLM이 아무것도 고르지 않아 점수순으로 대체합니다.")
        return candidates[:limit]

    selected = [candidates[index] for index in chosen[:limit]]

    # LLM이 하한보다 적게 골랐으면 점수 높은 나머지 기사로 채운다
    if len(selected) < min(_PICK_MIN, len(candidates)):
        already = {item["url"] for item in selected}
        selected += [item for item in candidates if item["url"] not in already][: _PICK_MIN - len(selected)]

    return selected


# "07:30" 형태의 문자열을 그 날짜의 datetime으로 바꾼다
def _at(day: date, hhmm: str) -> datetime:
    hour, minute = (int(part) for part in hhmm.split(":"))
    return datetime.combine(day, time(hour, minute), tzinfo=_KST)


# 이 슬롯이 담을 기사의 시간 구간을 구한다 (시작, 끝)
# 끝이 아직 안 온 시각이면(테스트로 미래 슬롯을 호출한 경우) 지금까지로 자른다
def _window(time_slot: str, trade_day: date, now: datetime) -> tuple[datetime, datetime]:
    start_hhmm, starts_yesterday = _SLOT_WINDOW[time_slot]
    start_day = trade_day - timedelta(days=1) if starts_yesterday else trade_day

    start = _at(start_day, start_hhmm)
    end = min(_at(trade_day, time_slot), now)
    return start, end


# 한 슬롯에 넣을 뉴스를 모아서 돌려준다
# time_slot: "07:30" 같은 슬롯 값. _SLOT_KEYWORDS에 없는 값을 넣으면 에러가 난다
# limit: 최종적으로 남길 기사 수의 상한 (기본 8). 하한 5건은 점수 상위 기사로 채워서 맞춘다
# trade_date: 어느 날의 슬롯인지. 안 넣으면 오늘
# now: 테스트할 때 특정 시각을 넣어보기 위한 값 - 평소에는 안 넣어도 된다
# use_llm: False로 주면 LLM 선별을 건너뛰고 점수 상위 N건을 그대로 쓴다 (키가 없거나 빠르게 확인할 때)
#
# 기사를 고르는 기준은 "직전 슬롯 이후에 나온 것"이다(_SLOT_WINDOW 참고).
# 구간 안에 기사가 너무 적으면 _FALLBACK_HOURS만큼 앞으로 넓혀서 다시 거른다
# 결과는 중요도 순서다 (앞에 있을수록 중요)
#
# 반환 형태:
#   [{"title": 제목, "summary": 요약, "url": 링크, "published_at": 발행시각, "score": 중요도}, ...]
#   score는 어떤 기사를 남길지 고를 때 쓴 값이다. 화면에는 안 쓰지만 왜 이 기사가 뽑혔는지
#   확인할 때 필요해서 같이 돌려준다
#   published_at은 기사 발행 시각이다. LLM에 기사 시점을 알려주는 데 쓰고,
#   timeline_news.published_at 칼럼에 저장해서 화면에도 내려간다
def collect(time_slot: str, *, limit: int = _PICK_MAX, trade_date: date | None = None, now: datetime | None = None, use_llm: bool = True) -> list[dict]:
    if time_slot not in _SLOT_KEYWORDS:
        raise ValueError(f"'{time_slot}'는 뉴스 검색어가 정해지지 않은 슬롯입니다 (_SLOT_KEYWORDS 확인).")

    now = now or datetime.now(_KST)
    start, end = _window(time_slot, trade_date or now.date(), now)

    # 검색어 여러 개의 결과를 합친다. 같은 기사가 여러 검색어에 걸리면 버리지 않고 점수를 더한다
    collected: dict[str, dict] = {}
    for keyword in _SLOT_KEYWORDS[time_slot]:
        for rank, item in enumerate(naver_client.search_news(keyword, display=_FETCH_PER_KEYWORD.get(time_slot, _FETCH_PER_KEYWORD_DEFAULT), sort="sim")["items"]):
            # link는 네이버 뉴스 주소, 없으면 언론사 원문 주소를 쓴다
            url = item["link"] or item["originallink"]
            if not url:
                continue

            if url in collected:
                collected[url]["score"] += 1 / (_RANK_BIAS + rank)
                continue

            collected[url] = {
                "title": _clean_text(item["title"]),
                "summary": _clean_text(item["description"]),
                "url": url,
                "published_at": _parse_pub_date(item["pubDate"]),
                "score": 1 / (_RANK_BIAS + rank),
            }

    # 구간에 드는 기사만 남긴다. 너무 적으면 시작을 앞으로 당겨서 한 번 더 걸러본다
    #
    # 끝을 배타적으로(< end) 잡는 이유
    #   양쪽을 포함으로 두면 슬롯 시각 정각에 발행된 기사가 두 슬롯에 모두 들어간다.
    #   예: 08:30:00 기사가 08:30 슬롯(07:30~08:30)과 09:30 슬롯(08:30~09:30)에 중복된다.
    #   구간을 나눠 중복을 0건으로 만든 설계인데 경계에 구멍이 남아 있었다.
    #   시작은 포함, 끝은 배타로 두면 [20:00, 07:30) [07:30, 08:30) 처럼 빈틈도 겹침도 없다
    picked = [item for item in collected.values() if start <= item["published_at"] < end]
    if len(picked) < _MIN_ITEMS:
        widened = end - timedelta(hours=_FALLBACK_HOURS)
        picked = [item for item in collected.values() if widened <= item["published_at"] < end]

    # 점수순으로 후보를 좁힌다
    #
    # 최신순으로 자르면 안 되는 이유: 07:30 슬롯은 구간이 11시간이 넘어서, 밤사이 나온 중요한 기사가
    # 아침에 쏟아진 자잘한 기사에 밀려 잘려나간다
    picked.sort(key=lambda x: x["score"], reverse=True)
    candidates = picked[: _CANDIDATE_LIMITS.get(time_slot, _CANDIDATE_LIMIT_DEFAULT)]

    # LLM이 후보 중에서 실제로 실을 기사를 고른다
    # 점수는 순위를 합칠 뿐 내용을 판단하지 못한다. '코스닥' 검색어에 걸린 정치인 발언 기사처럼
    # 시황과 무관한 기사는 여기서 걸러진다
    selected = _select_with_llm(time_slot, candidates, limit) if use_llm else candidates[:limit]

    # 화면에는 이 순서 그대로 나간다. 중요한 기사가 앞이다
    # 최신순으로 다시 세우지 않는 이유: 타임라인 슬롯 자체가 이미 시간대를 나눠놓은 구조라,
    # 그 안에서까지 시간순으로 볼 이유가 없다. 무엇이 중요한지가 더 유용하다
    return selected
