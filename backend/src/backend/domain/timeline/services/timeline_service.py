# timeline_service.py
# 슬롯 하나에 들어갈 데이터를 모아서 응답 형태로 조립한다
#
# 경로가 두 개다
#   collect_and_save()  스케줄러가 정해진 시각에 부른다. 수집 -> DB 저장 -> 저장된 값을 응답
#   get_day()           프런트가 부른다. DB에서 읽기만 한다
#
# get_slot()은 DB를 거치지 않고 즉석 수집해서 돌려주는 확인용 경로다.
# 값이 호출할 때마다 조금씩 달라지므로 화면용으로 쓰지 말 것

import asyncio
import logging
import time
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.timeline.schemas.timeline import (
    BeginnerGuideItem,
    BriefingPointItem,
    IntradayChangeItem,
    LeadingSectorItem,
    LeadingSectorStockItem,
    NewsItem,
    SlotIndicatorItem,
    TimelineSlotResponse,
    TopGainerItem,
)
from backend.core.database import get_session_factory
from backend.domain.timeline.models.timeline import TimelineSlot
from backend.domain.timeline.services import briefing_service, leading_sector_service, market_hours, market_indicator_service, news_service, prompts, timeline_repository, top_gainer_service

# 슬롯 정의. (URL에 쓰는 값) -> (DB에 저장하는 값, 화면에 보여줄 명칭)
#
# URL에 콜론을 못 쓰기 때문에 "0730"으로 받고, DB에는 "07:30" 형태로 저장한다.
# 명칭은 고정 문구라 프런트에서 매핑해도 되지만, 응답만 봐도 어느 슬롯인지 알 수 있게 같이 내려준다.
#
# 명칭은 prompts.SLOT_TITLES 하나만 보고 만든다. 두 곳에 따로 적어두면 한쪽만 고쳐서 어긋난다
_SLOT_DEFS = {time_slot.replace(":", ""): (time_slot, title) for time_slot, title in prompts.SLOT_TITLES.items()}

# 주도 섹터를 뽑는 슬롯 (정규장 09:00~15:30 안에 있는 슬롯만)
#
# 거래소가 업종 지수를 정규장에만 산출하기 때문이다. 2026-09-11에 실측으로 확인했다.
#   07:46(프리마켓 전)과 08:56(프리마켓 후)에 업종 21개 등락률이 전부 0.00%로 동일했고,
#   전날 23:36에는 마지막 체결이 15:32에 멈춰 있었다.
#
# 나머지 슬롯 처리
#   07:30 - 아무것도 안 넣는다. 이 시간대는 "어제 마감 & 글로벌 현황"(지표 6종)이 그 자리를 대신한다
#   08:30 / 17:30 / 20:00 - 급상승 종목으로 대체한다 (top_gainer_service 참고)
_SLOTS_WITH_LEADING_SECTOR = {"0930", "1200", "1400", "1530"}

# 지표 6종을 넣는 슬롯 (07:30 "어제 마감 & 글로벌 현황")
#
# 이 시간에는 환율 빼고 전 시장이 닫혀 있어서, 지수 5종은 어제 국내 종가와 밤사이 미국 마감값이
# 그대로 남아 있다. 슬롯 성격과 정확히 맞는다.
#
# 그래도 캐시를 읽지 않고 새로 받는다(force_refresh=True). 환율 때문이다.
#   환율은 24시간 움직여서 캐시 값이 최대 10분 낡을 수 있다. 게다가 지표 바 갱신 작업이
#   07:30 정각에 같이 예약돼 있어서(cron minute=0,10,...,30,...) 어느 쪽이 먼저 끝날지 모른다.
#   캐시를 읽으면 07:20 환율이 "07:30 가격"으로 저장될 수 있다.
#
#   이 값은 15:30 장중 변화의 기준점이고, **그 시점을 놓치면 되살릴 방법이 없다**
#   (코스피·코스닥은 07:30 값이 곧 전일 종가라 복원되지만 환율은 안 된다).
#   15:30 슬롯도 같은 이유로 새로 받으므로, 두 시점을 같은 방식으로 재는 것이 맞다.
#   대가는 하루 6회 추가 호출이다
_SLOTS_WITH_INDICATORS = {"0730"}

# 장중 변화를 넣는 슬롯 (15:30 "장 마감")
# 07:30 가격과 지금 가격을 비교해서 그날 장중에 얼마나 움직였는지 보여준다.
# 07:30 슬롯이 DB에 저장돼 있어야 만들 수 있다 - 07:30 가격을 거기서 읽어오기 때문
_SLOTS_WITH_INTRADAY = {"1530"}

# 장중 변화에 넣을 지표 이름 (지표 6종 중 이 셋만 쓴다)
# market_indicator_service의 _INDICATOR_DEFS에 적힌 화면 이름과 같아야 한다
_INTRADAY_TARGET_NAMES = ("KOSPI", "KOSDAQ", "USD/KRW")

# 슬롯별 수집 시각. (slot_key) -> (시, 분)
#
# 여덟 슬롯 모두 슬롯 시각 정시에 수집한다. 생성에 1~2분 걸리므로(거래일 실측 78초)
# 화면에는 그만큼 늦게 뜬다.
#
# 처음에는 5분 전에 미리 만들어두는 방식이었는데 바꿨다. 이유는 세 가지다.
#   1. 데이터가 슬롯 시각과 어긋난다. "12:00 오전장 흐름"에 11:55 값이 들어간다.
#      화면 노출은 지나가면 끝이지만 저장된 데이터는 영구히 남는다.
#   2. 뉴스 구간이 잘린다. 12:00 슬롯의 구간은 09:30~12:00인데 11:55에 수집하면 마지막 5분이 빠진다.
#   3. 미리 만드는 방식은 마감이 있다. 07:25에 실패하면 07:30까지 5분 안에 성공해야 한다.
#      정시 수집은 마감이 없어서 실패해도 다시 시도하고 조금 늦게 올리면 된다.
#
# 15:30도 정시로 통일했다 (2026-09-12)
#   전에는 15:35였다. 코스피 종가는 15:20~15:30 마감 동시호가로 정해지므로 정시에 조회하면
#   마감 전 값이 들어갈 수 있다는 우려였는데, 그 차이가 실제로 있는지는 재본 적이 없다.
#   슬롯 여덟 개 중 하나만 규칙이 다른 상태를 유지하는 대가가 더 크다고 판단했다.
#   장중 변화는 캐시가 아니라 새로 받아오므로(_indicator_rows(force_refresh=True)) 15:30:00
#   시점의 최신 값이 들어간다.
#
#   월요일(9/14) 실데이터에서 15:30 슬롯의 closing_price와 실제 종가를 비교해볼 것.
#   다르면 이 표의 "1530"만 (15, 35)로 되돌리면 된다
#
# 수집 시각을 바꾸려면 이 표만 고치면 된다
SLOT_COLLECT_TIMES = {
    "0730": (7, 30),
    "0830": (8, 30),
    "0930": (9, 30),
    "1200": (12, 0),
    "1400": (14, 0),
    "1530": (15, 30),
    "1730": (17, 30),
    "2000": (20, 0),
}

# 슬롯 하나에 넣을 뉴스 개수 (최대 8건, 최소 5건)
# 두 곳에 숫자를 따로 적어두면 한쪽만 고쳐서 어긋나므로 news_service의 상한을 그대로 가져다 쓴다
_NEWS_LIMIT = news_service._PICK_MAX

_KST = ZoneInfo("Asia/Seoul")

logger = logging.getLogger(__name__)


# 단계별 소요 시간을 재서 찍고 결과를 그대로 돌려준다
#
# 슬롯 하나를 만드는 데 1~2분이 걸리는데(거래일 실측 78초), 어디서 시간을 쓰는지 총시간만으로는
# 모른다. 느려지거나 실패했을 때 KIS인지 네이버인지 제미나이인지 바로 가르려면 단계별로 필요하다
def _timed(label: str, func, *args, **kwargs):
    started = time.monotonic()
    result = func(*args, **kwargs)
    logger.info("  [%s] %.1f초", label, time.monotonic() - started)
    return result


# 주도 섹터 수집 결과를 응답 형태로 바꾼다
def _to_sector_items(collected: list[dict]) -> list[LeadingSectorItem]:
    return [
        LeadingSectorItem(
            name=sector["name"],
            change_rate=sector["change_rate"],
            stocks=[LeadingSectorStockItem(**stock) for stock in sector["stocks"]],
        )
        for sector in collected
    ]


# 지표 캐시에서 필요한 값만 뽑는다 (LLM 입력과 응답에 같이 쓴다)
#
# 캐시가 비어 있으면 먼저 채운다. 캐시는 서버가 뜰 때(main.py의 lifespan) 채워지는데,
# 스케줄러가 아닌 다른 경로로 이 함수가 불릴 수 있다(스크립트 실행, 서버 기동 직후 등).
# 이 처리가 없으면 07:30 슬롯의 지표가 조용히 빈 채로 저장된다 - 실제로 그렇게 저장된 적이 있다
#
# force_refresh=True면 캐시가 차 있어도 KIS를 다시 부른다. 15:30 슬롯의 장중 변화에 쓴다.
# 그 슬롯은 15:35에 수집하는데 캐시는 15:30에 갱신된 뒤 15:40에는 장마감으로 건너뛰므로,
# 캐시를 그대로 읽으면 마감 동시호가 전 값이 "종가"로 저장된다.
# 15:30을 5분 미뤄둔 이유 자체가 확정된 종가를 받기 위해서라서, 여기서는 새로 불러야 한다.
# KIS를 6번 부르므로 이벤트 루프를 막지 않도록 호출하는 쪽에서 asyncio.to_thread로 감쌀 것
def _indicator_rows(*, force_refresh: bool = False) -> list[dict]:
    if force_refresh or not market_indicator_service.get_cache_snapshot():
        market_indicator_service.refresh_all(force=True)

    return [{"code": cached["code"], "name": cached["name"], "price": cached["price"], "change_rate": cached["change_rate"]} for cached in market_indicator_service.get_cache_snapshot().values()]


# 뉴스 수집 결과에서 응답에 쓸 필드만 남긴다 (score는 고르는 데만 쓰고 화면에는 안 나간다)
def _news_fields(rows: list[dict]) -> list[dict]:
    return [{"title": row["title"], "summary": row["summary"], "url": row["url"], "published_at": row["published_at"]} for row in rows]


# 장중 변화를 계산한다 (07:30 가격 vs 지금 가격)
#
# 07:30 슬롯이 DB에 없으면 빈 목록을 돌려준다. 그날 07:30 수집이 실패했거나 서버가 꺼져 있었던
# 경우인데, 07:30 시점의 환율은 지나가면 되살릴 수 없어서 나중에 복구할 방법이 없다.
# (코스피·코스닥은 07:30 값이 곧 전일 종가라 복원 가능하지만, 환율은 24시간 움직여서 불가능하다)
# 그래서 07:30 슬롯 수집이 실패하면 재시도로 반드시 채워두는 것이 중요하다
async def _intraday_rows(session: AsyncSession, trade_date: date, current: list[dict]) -> list[dict]:
    morning = await timeline_repository.load_slot(session, trade_date, "07:30")
    if morning is None:
        logger.warning("%s 07:30 슬롯이 없어 장중 변화를 만들 수 없습니다.", trade_date)
        return []

    morning_prices = {row.name: row.price for row in morning.indicators}

    rows = []
    for item in current:
        if item["name"] not in _INTRADAY_TARGET_NAMES:
            continue

        morning_price = morning_prices.get(item["name"])
        if not morning_price:  # 값이 없거나 0이면 변동폭을 계산할 수 없다
            continue

        rows.append(
            {
                "name": item["name"],
                "morning_price": morning_price,
                "closing_price": item["price"],
                "change_rate": (item["price"] - morning_price) / morning_price * 100,
            }
        )
    return rows


# 슬롯 하나에 들어갈 데이터를 모은다 (DB 저장과 즉석 응답이 같이 쓴다)
# slot_key: URL로 받은 값 ("0730" 등). _SLOT_DEFS에 없으면 ValueError를 낸다
#
# LLM을 세 번 부르기 때문에(뉴스 선별 + 브리핑 + 불개미 요약) 1~2분 걸린다.
# with_briefing=False를 주면 LLM 단계를 통째로 건너뛴다 - 수집 결과만 빠르게 볼 때 쓴다
#
# 반환 형태: {"briefing": ..., "beginner_guides": [...], "news": [...], "indicators": [...],
#             "leading_sectors": [...], "top_gainers": [...], "intraday_changes": [...]}
def collect_slot(slot_key: str, *, with_briefing: bool = True, intraday_changes: list[dict] | None = None) -> dict:
    if slot_key not in _SLOT_DEFS:
        raise ValueError(f"'{slot_key}'는 없는 슬롯입니다. 가능한 값: {', '.join(_SLOT_DEFS)}")

    # 장중 변화는 DB에서 07:30 값을 읽어야 만들 수 있어서 여기서 만들지 않고 넘겨받는다.
    # 브리핑이 이 값을 재료로 써야 하므로 브리핑보다 먼저 준비돼 있어야 한다(collect_and_save 참고)
    intraday_changes = intraday_changes or []

    time_slot, _ = _SLOT_DEFS[slot_key]
    logger.info("[수집] %s 시작", time_slot)
    total_started = time.monotonic()

    sectors = _timed("주도 섹터", leading_sector_service.collect) if slot_key in _SLOTS_WITH_LEADING_SECTOR else []
    indicators = _timed("지표 6종", _indicator_rows, force_refresh=True) if slot_key in _SLOTS_WITH_INDICATORS else []
    top_gainers = _timed("급상승 종목", top_gainer_service.collect, slot_key) if slot_key in top_gainer_service.SOURCE_BY_SLOT else []
    news = _timed("뉴스", news_service.collect, time_slot, limit=_NEWS_LIMIT, use_llm=with_briefing)

    # 브리핑은 위에서 모은 값을 재료로 쓴다. 그래서 수집이 끝난 뒤에 부른다
    if with_briefing:
        briefing, guides = _timed(
            "LLM 브리핑·해설",
            briefing_service.generate,
            time_slot,
            indicators=indicators,
            sectors=sectors,
            top_gainers=top_gainers,
            intraday_changes=intraday_changes,
            news=news,
        )
    else:
        briefing, guides = None, []

    logger.info("[수집] %s 완료 - 총 %.1f초", time_slot, time.monotonic() - total_started)

    return {
        "briefing": briefing,
        "beginner_guides": guides,
        "news": _news_fields(news),
        "indicators": indicators,
        "leading_sectors": sectors,
        "top_gainers": top_gainers,
        "intraday_changes": intraday_changes,
    }


# 수집한 값을 응답 형태로 바꾼다 (DB를 거치지 않는 즉석 조회용)
def _to_response(slot_key: str, collected: dict) -> TimelineSlotResponse:
    time_slot, title = _SLOT_DEFS[slot_key]
    briefing = collected["briefing"]

    return TimelineSlotResponse(
        slot_key=slot_key,
        time_slot=time_slot,
        title=title,
        collected_at=datetime.now(UTC),
        briefing_headline=briefing["headline"] if briefing else None,
        briefing_subtitle=briefing["subtitle"] if briefing else None,
        briefing_points=[BriefingPointItem(**point) for point in (briefing["points"] if briefing else [])],
        beginner_guides=[BeginnerGuideItem(**guide) for guide in collected["beginner_guides"]],
        leading_sectors=_to_sector_items(collected["leading_sectors"]),
        top_gainers=[TopGainerItem(**row) for row in collected["top_gainers"]],
        news=[NewsItem(seq=seq, **item) for seq, item in enumerate(collected["news"], start=1)],
        indicators=[SlotIndicatorItem(name=row["name"], price=row["price"], change_rate=row["change_rate"]) for row in collected["indicators"]],
        intraday_changes=[IntradayChangeItem(**row) for row in collected["intraday_changes"]],
    )


# DB를 거치지 않고 지금 수집해서 바로 돌려준다 (확인용 엔드포인트가 쓴다)
def get_slot(slot_key: str, *, with_briefing: bool = True) -> TimelineSlotResponse:
    return _to_response(slot_key, collect_slot(slot_key, with_briefing=with_briefing))


# DB에 저장된 시각에 한국 시간임을 붙여준다
#
# DB에는 시간대 정보 없이 한국 시간 시계값만 저장한다(models/timeline.py 참고).
# 그대로 내보내면 프런트가 무슨 시간대인지 몰라서 UTC로 읽을 수 있으므로, 꺼낼 때 붙여준다
def _with_kst(value: datetime | None) -> datetime | None:
    return value.replace(tzinfo=_KST) if value is not None else None


# DB에서 읽은 슬롯을 응답 형태로 바꾼다
def _from_db(slot: TimelineSlot) -> TimelineSlotResponse:
    slot_key = slot.time_slot.replace(":", "")

    return TimelineSlotResponse(
        slot_key=slot_key,
        time_slot=slot.time_slot,
        title=prompts.SLOT_TITLES.get(slot.time_slot, slot.time_slot),
        collected_at=_with_kst(slot.created_at),
        briefing_headline=slot.briefing_headline,
        briefing_subtitle=slot.briefing_subtitle,
        briefing_points=[BriefingPointItem(seq=row.seq, title=row.title, body=row.body) for row in slot.insights],
        beginner_guides=[
            BeginnerGuideItem(
                seq=row.seq,
                title=row.title,
                body=row.body,
                # 저장할 때 쉼표로 이어붙였으므로 꺼낼 때 다시 나눈다
                tags=[tag.strip() for tag in (row.tags or "").split(",") if tag.strip()],
            )
            for row in slot.beginner_guides
        ],
        leading_sectors=[
            LeadingSectorItem(
                name=sector.name,
                change_rate=sector.change_rate,
                stocks=[LeadingSectorStockItem(name=stock.name, change_rate=stock.change_rate, label=stock.label) for stock in sector.stocks],
            )
            for sector in slot.leading_sectors
        ],
        top_gainers=[TopGainerItem(seq=row.seq, name=row.name, change_rate=row.change_rate, price=row.price) for row in slot.top_gainers],
        news=[NewsItem(seq=row.seq, title=row.title, summary=row.summary or "", url=row.url, published_at=_with_kst(row.published_at)) for row in slot.news],
        indicators=[SlotIndicatorItem(name=row.name, price=row.price, change_rate=row.change_rate) for row in slot.indicators],
        intraday_changes=[IntradayChangeItem(name=row.name, morning_price=row.morning_price, closing_price=row.closing_price, change_rate=row.change_rate) for row in slot.intraday_changes],
    )


# 슬롯을 수집해서 DB에 저장한다. 스케줄러가 정해진 시각에 호출할 함수다
# trade_date: 어느 거래일로 저장할지. 안 넣으면 오늘(한국 시간 기준)
async def collect_and_save(session: AsyncSession, slot_key: str, *, trade_date: date | None = None, with_briefing: bool = True) -> TimelineSlotResponse:
    if slot_key not in _SLOT_DEFS:
        raise ValueError(f"'{slot_key}'는 없는 슬롯입니다. 가능한 값: {', '.join(_SLOT_DEFS)}")

    time_slot, _ = _SLOT_DEFS[slot_key]
    day = trade_date or datetime.now(_KST).date()

    # 장중 변화를 먼저 만든다 (15:30 슬롯만)
    #
    # 순서가 중요하다. 이 값이 브리핑의 재료이기 때문이다. 예전에는 수집·브리핑이 끝난 뒤에
    # 채웠는데, 그러면 "장 마감" 브리핑이 07:30 대비 하루 움직임을 못 보고 뉴스와 섹터만 보고
    # 글을 썼다. 그날 시장이 얼마나 움직였는지가 마감 브리핑의 핵심 재료다.
    #
    # 지표는 캐시에서 읽지 않고 새로 부른다(force_refresh=True). 캐시는 10분 주기로 갱신되는데,
    # 지표 바 갱신 작업과 이 슬롯이 15:30 정각에 동시에 예약돼 있어서 어느 쪽이 먼저 끝날지
    # 알 수 없다. 캐시를 읽으면 15:20 값이 종가로 저장될 수 있다
    intraday = []
    if slot_key in _SLOTS_WITH_INTRADAY:
        closing = await asyncio.to_thread(_indicator_rows, force_refresh=True)
        intraday = await _intraday_rows(session, day, closing)

    # 수집은 동기 함수라 별도 스레드에서 돌린다
    # 그냥 부르면 KIS·네이버·LLM 요청(1~2분)이 이벤트 루프를 통째로 막아서, 그동안 서버가
    # 아무 요청도 못 받고 다른 예약 작업도 멈춘다
    collected = await asyncio.to_thread(collect_slot, slot_key, with_briefing=with_briefing, intraday_changes=intraday)

    saved = await timeline_repository.save_slot(session, day, time_slot, collected)
    return _from_db(saved)


# 하루치 슬롯을 DB에서 꺼낸다. 프런트가 호출하는 조회용
#
# 오늘 날짜를 조회할 때는 아직 시간이 안 된 슬롯을 빼고 돌려준다. 지난 날짜는 전부 내려준다.
#
# 지금은 슬롯 시각에 수집을 시작하므로 시각보다 먼저 데이터가 생길 일이 없다. 그래도 이 필터를
# 남겨두는 이유는, 확인용으로 미래 슬롯을 수동 수집(POST /timeline/collect)했을 때를 막기 위해서다
def _visible(slots: list[TimelineSlot], trade_date: date, now: datetime) -> list[TimelineSlot]:
    if trade_date != now.date():
        return slots

    current = f"{now:%H:%M}"
    return [slot for slot in slots if slot.time_slot <= current]


# 하루치 슬롯 조회
async def get_day(session: AsyncSession, trade_date: date, *, now: datetime | None = None) -> list[TimelineSlotResponse]:
    slots = await timeline_repository.load_day(session, trade_date)
    return [_from_db(slot) for slot in _visible(slots, trade_date, now or datetime.now(_KST))]


# 화면에 쓸 슬롯 목록 (어떤 slot_key를 호출하면 되는지 확인용)
def get_slot_list() -> list[dict]:
    return [{"slot_key": key, "time_slot": time_slot, "title": title} for key, (time_slot, title) in _SLOT_DEFS.items()]


# 스케줄러가 정해진 시각에 부르는 함수
#
# 여기서 세 가지를 처리한다
#   1. 휴장일이면 아무것도 하지 않는다 (주말·공휴일에 빈 데이터가 쌓이는 것을 막는다)
#   2. DB 세션을 직접 만든다 (엔드포인트와 달리 요청이 없으므로 Depends를 쓸 수 없다)
#   3. 실패해도 예외를 밖으로 내보내지 않는다 - 한 슬롯이 실패해도 다른 슬롯 예약은 살아있어야 한다
async def run_scheduled_collect(slot_key: str) -> None:
    if not market_hours.is_trading_day():
        logger.info("[스케줄러] %s 건너뜀 - 오늘은 장이 열리지 않습니다.", slot_key)
        return

    started = datetime.now(_KST)
    try:
        async with get_session_factory()() as session:
            saved = await collect_and_save(session, slot_key)
    except Exception as error:
        # exc_info=True로 스택까지 남긴다. 슬롯이 통째로 실패한 경우라 원인 추적이 필요하다
        logger.error("[스케줄러] %s 수집 실패 - %s: %s", slot_key, type(error).__name__, error, exc_info=True)
        return

    seconds = (datetime.now(_KST) - started).total_seconds()
    logger.info(
        "[스케줄러] %s %s 저장 완료 (%.0f초) - 뉴스 %d건, 브리핑 %s",
        saved.time_slot, saved.title, seconds, len(saved.news), "있음" if saved.briefing_headline else "없음",
    )
