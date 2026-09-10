# timeline_service.py
# 슬롯 하나에 들어갈 데이터를 모아서 응답 형태로 조립한다
#
# 지금은 DB를 거치지 않는다. 요청이 올 때마다 주도 섹터·뉴스를 새로 수집하고 지표는 캐시에서 읽어서
# 바로 내려준다. Postman으로 값이 제대로 나오는지 확인하는 단계이기 때문이다.
# 저장 로직(timeline_slot 테이블에 넣기)과 스케줄러 연결은 다음 단계에서 붙인다.

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
)
from backend.domain.timeline.models.timeline import TimelineSlot
from backend.domain.timeline.services import briefing_service, leading_sector_service, market_indicator_service, news_service, prompts, timeline_repository

# 슬롯 정의. (URL에 쓰는 값) -> (DB에 저장하는 값, 화면에 보여줄 명칭)
#
# URL에 콜론을 못 쓰기 때문에 "0730"으로 받고, DB에는 "07:30" 형태로 저장한다.
# 명칭은 고정 문구라 프런트에서 매핑해도 되지만, 응답만 봐도 어느 슬롯인지 알 수 있게 같이 내려준다.
#
# 명칭은 prompts.SLOT_TITLES 하나만 보고 만든다. 두 곳에 따로 적어두면 한쪽만 고쳐서 어긋난다
_SLOT_DEFS = {time_slot.replace(":", ""): (time_slot, title) for time_slot, title in prompts.SLOT_TITLES.items()}

# 주도 섹터를 뽑지 않는 슬롯
# 이 시간대는 장이 열리기 전이라 업종 등락률이 전일 값 그대로다. 게다가 업종 지수 API는 프리마켓
# (넥스트레이드)을 아예 지원하지 않아서(NX 코드 거부, 확인 완료) 가져올 값 자체가 없다
_SLOTS_WITHOUT_LEADING_SECTOR = {"0730", "0830"}

# 지표 6종을 넣는 슬롯 (07:30 "어제 마감 & 글로벌 현황")
# 이 시간에는 환율 빼고 전 시장이 닫혀 있어서 지표 캐시에 어제 국내 종가와 밤사이 미국 마감값이
# 그대로 남아 있다. 슬롯 성격과 정확히 맞으므로 KIS를 다시 부르지 않고 캐시를 그대로 쓴다
_SLOTS_WITH_INDICATORS = {"0730"}

# 장중 변화를 넣는 슬롯 (15:30 "장 마감")
# 07:30 가격과 지금 가격을 비교해서 그날 장중에 얼마나 움직였는지 보여준다.
# 07:30 슬롯이 DB에 저장돼 있어야 만들 수 있다 - 07:30 가격을 거기서 읽어오기 때문
_SLOTS_WITH_INTRADAY = {"1530"}

# 장중 변화에 넣을 지표 이름 (지표 6종 중 이 셋만 쓴다)
# market_indicator_service의 _INDICATOR_DEFS에 적힌 화면 이름과 같아야 한다
_INTRADAY_TARGET_NAMES = ("KOSPI", "KOSDAQ", "USD/KRW")

# 슬롯 하나에 넣을 뉴스 개수
_NEWS_LIMIT = 10

_KST = ZoneInfo("Asia/Seoul")


# 주도 섹터 수집 결과를 응답 형태로 바꾼다
def _to_sector_items(collected: list[dict]) -> list[LeadingSectorItem]:
    return [
        LeadingSectorItem(
            code=sector["code"],
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
def _indicator_rows() -> list[dict]:
    if not market_indicator_service.get_cache_snapshot():
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
        print(f"[경고] {trade_date} 07:30 슬롯이 없어 장중 변화를 만들 수 없습니다.")
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
# LLM을 두 번 부르기 때문에 1분 안팎 걸린다.
# with_briefing=False를 주면 LLM 단계를 통째로 건너뛴다 - 수집 결과만 빠르게 볼 때 쓴다
#
# 반환 형태: {"briefing": ..., "beginner_guides": [...], "news": [...], "indicators": [...], "leading_sectors": [...]}
def collect_slot(slot_key: str, *, with_briefing: bool = True) -> dict:
    if slot_key not in _SLOT_DEFS:
        raise ValueError(f"'{slot_key}'는 없는 슬롯입니다. 가능한 값: {', '.join(_SLOT_DEFS)}")

    time_slot, _ = _SLOT_DEFS[slot_key]

    sectors = [] if slot_key in _SLOTS_WITHOUT_LEADING_SECTOR else leading_sector_service.collect()
    indicators = _indicator_rows() if slot_key in _SLOTS_WITH_INDICATORS else []
    news = news_service.collect(time_slot, limit=_NEWS_LIMIT, use_llm=with_briefing)

    # 브리핑은 위에서 모은 값을 재료로 쓴다. 그래서 수집이 끝난 뒤에 부른다
    briefing, guides = briefing_service.generate(time_slot, indicators=indicators, sectors=sectors, news=news) if with_briefing else (None, [])

    return {
        "briefing": briefing,
        "beginner_guides": guides,
        "news": _news_fields(news),
        "indicators": indicators,
        "leading_sectors": sectors,
        # 장중 변화는 DB에서 07:30 값을 읽어야 만들 수 있어서 여기서는 비워두고 collect_and_save에서 채운다
        "intraday_changes": [],
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
        news=[NewsItem(seq=seq, **item) for seq, item in enumerate(collected["news"], start=1)],
        indicators=[SlotIndicatorItem(**row) for row in collected["indicators"]],
        intraday_changes=[IntradayChangeItem(**row) for row in collected["intraday_changes"]],
    )


# DB를 거치지 않고 지금 수집해서 바로 돌려준다 (확인용 엔드포인트가 쓴다)
def get_slot(slot_key: str, *, with_briefing: bool = True) -> TimelineSlotResponse:
    return _to_response(slot_key, collect_slot(slot_key, with_briefing=with_briefing))


# DB에서 읽은 슬롯을 응답 형태로 바꾼다
def _from_db(slot: TimelineSlot) -> TimelineSlotResponse:
    slot_key = slot.time_slot.replace(":", "")

    return TimelineSlotResponse(
        slot_key=slot_key,
        time_slot=slot.time_slot,
        title=prompts.SLOT_TITLES.get(slot.time_slot, slot.time_slot),
        collected_at=slot.created_at,
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
                code="",  # 업종코드는 저장하지 않는다(화면에 안 쓰는 값이라 테이블에 칸이 없음)
                name=sector.name,
                change_rate=sector.change_rate,
                stocks=[LeadingSectorStockItem(name=stock.name, change_rate=stock.change_rate, label=stock.label) for stock in sector.stocks],
            )
            for sector in slot.leading_sectors
        ],
        # published_at은 테이블에 칸이 없어서 저장한 시각으로 채운다
        news=[NewsItem(seq=row.seq, title=row.title, summary=row.summary or "", url=row.url, published_at=slot.created_at) for row in slot.news],
        indicators=[SlotIndicatorItem(code="", name=row.name, price=row.price, change_rate=row.change_rate) for row in slot.indicators],
        intraday_changes=[IntradayChangeItem(name=row.name, morning_price=row.morning_price, closing_price=row.closing_price, change_rate=row.change_rate) for row in slot.intraday_changes],
    )


# 슬롯을 수집해서 DB에 저장한다. 스케줄러가 정해진 시각에 호출할 함수다
# trade_date: 어느 거래일로 저장할지. 안 넣으면 오늘(한국 시간 기준)
async def collect_and_save(session: AsyncSession, slot_key: str, *, trade_date: date | None = None, with_briefing: bool = True) -> TimelineSlotResponse:
    if slot_key not in _SLOT_DEFS:
        raise ValueError(f"'{slot_key}'는 없는 슬롯입니다. 가능한 값: {', '.join(_SLOT_DEFS)}")

    time_slot, _ = _SLOT_DEFS[slot_key]
    day = trade_date or datetime.now(_KST).date()
    collected = collect_slot(slot_key, with_briefing=with_briefing)

    # 장중 변화는 그날 07:30 슬롯을 읽어야 하므로 저장 직전에 채운다
    if slot_key in _SLOTS_WITH_INTRADAY:
        collected["intraday_changes"] = await _intraday_rows(session, day, _indicator_rows())

    saved = await timeline_repository.save_slot(session, day, time_slot, collected)
    return _from_db(saved)


# 하루치 슬롯을 DB에서 꺼낸다. 프런트가 호출하는 조회용
#
# 오늘 날짜를 조회할 때는 아직 시간이 안 된 슬롯을 빼고 돌려준다.
# 데이터는 슬롯 시각 5분 전에 미리 만들어두기 때문에, 이 필터가 없으면 07:26에 07:30 슬롯이
# 먼저 보여버린다. 지난 날짜는 전부 내려준다
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
