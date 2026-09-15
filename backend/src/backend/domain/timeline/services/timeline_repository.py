# timeline_repository.py
# 타임라인 슬롯의 DB 저장·조회만 담당한다. 수집·가공은 timeline_service에 있다.

import logging
from datetime import date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.domain.timeline.models.timeline import (
    TimelineBeginnerGuide,
    TimelineBriefingInsight,
    TimelineIndicator,
    TimelineIntradayChange,
    TimelineLeadingSector,
    TimelineLeadingSectorStock,
    TimelineNews,
    TimelineSlot,
    TimelineTopGainer,
)

_KST = ZoneInfo("Asia/Seoul")

logger = logging.getLogger(__name__)


# 시각을 시간대 없는 한국 시간으로 바꾼다 (DB 저장 형식)
def _to_naive_kst(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.astimezone(_KST).replace(tzinfo=None)


# 슬롯을 읽을 때 같이 읽어올 자식 테이블
# 비동기 ORM은 나중에 자식을 꺼내면 MissingGreenlet 에러가 나서 미리 읽어야 한다
# 테이블을 추가하면 여기에도 넣을 것 (빠뜨리면 그 값만 빈 채로 응답된다)
_EAGER_LOAD = (
    selectinload(TimelineSlot.insights),
    selectinload(TimelineSlot.beginner_guides),
    selectinload(TimelineSlot.news),
    selectinload(TimelineSlot.indicators),
    selectinload(TimelineSlot.intraday_changes),
    selectinload(TimelineSlot.leading_sectors).selectinload(TimelineLeadingSector.stocks),
    selectinload(TimelineSlot.top_gainers),
)


# 슬롯을 저장하고 저장된 슬롯을 돌려준다
# 같은 날 같은 시간대가 있으면 지우고 새로 넣는다 (자식 행은 cascade로 같이 지워진다)
# 새 브리핑·해설이 비어 있으면 기존 값을 유지한다 (LLM 실패로 재수집할 때 멀쩡한 브리핑을 지우지 않도록)
# collected: timeline_service.collect_slot의 반환값
async def save_slot(session: AsyncSession, trade_date: date, time_slot: str, collected: dict) -> TimelineSlot:
    existing = await session.scalar(
        select(TimelineSlot).where(TimelineSlot.trade_date == trade_date, TimelineSlot.time_slot == time_slot).options(*_EAGER_LOAD)
    )

    briefing = collected.get("briefing")
    guides = collected.get("beginner_guides", [])

    if briefing is None and existing is not None and existing.briefing_headline:
        briefing = {
            "headline": existing.briefing_headline,
            "subtitle": existing.briefing_subtitle,
            "points": [{"seq": row.seq, "title": row.title, "body": row.body} for row in existing.insights],
        }
        logger.info("%s %s - 새 브리핑이 없어서 기존 브리핑을 유지합니다.", trade_date, time_slot)

    if not guides and existing is not None and existing.beginner_guides:
        guides = [
            {"seq": row.seq, "title": row.title, "body": row.body, "tags": [tag.strip() for tag in (row.tags or "").split(",") if tag.strip()]}
            for row in existing.beginner_guides
        ]

    if existing is not None:
        await session.delete(existing)
        await session.flush()  # 삭제를 먼저 반영해야 새 행이 유니크 제약에 걸리지 않는다
    slot = TimelineSlot(
        trade_date=trade_date,
        time_slot=time_slot,
        briefing_headline=briefing["headline"] if briefing else None,
        briefing_subtitle=briefing["subtitle"] if briefing else None,
    )

    if briefing:
        slot.insights = [TimelineBriefingInsight(seq=point["seq"], title=point["title"], body=point["body"]) for point in briefing["points"]]

    slot.beginner_guides = [
        TimelineBeginnerGuide(
            seq=guide["seq"],
            title=guide["title"],
            body=guide["body"],
            # 태그 목록을 쉼표로 이어 한 칸에 저장한다
            tags=", ".join(guide["tags"]) or None,
        )
        for guide in guides
    ]

    slot.news = [TimelineNews(seq=seq, title=item["title"], summary=item["summary"], url=item["url"], published_at=_to_naive_kst(item.get("published_at"))) for seq, item in enumerate(collected.get("news", []), start=1)]

    slot.indicators = [TimelineIndicator(name=item["name"], price=item["price"], change_rate=item["change_rate"]) for item in collected.get("indicators", [])]

    slot.top_gainers = [
        TimelineTopGainer(seq=item["seq"], name=item["name"], change_rate=item["change_rate"], price=item["price"])
        for item in collected.get("top_gainers", [])
    ]

    slot.intraday_changes = [
        TimelineIntradayChange(name=item["name"], morning_price=item["morning_price"], closing_price=item["closing_price"], change_rate=item["change_rate"])
        for item in collected.get("intraday_changes", [])
    ]

    slot.leading_sectors = [
        TimelineLeadingSector(
            name=sector["name"],
            change_rate=sector["change_rate"],
            stocks=[TimelineLeadingSectorStock(name=stock["name"], change_rate=stock["change_rate"], label=stock["label"]) for stock in sector["stocks"]],
        )
        for sector in collected.get("leading_sectors", [])
    ]

    session.add(slot)
    await session.commit()

    # 자식 테이블까지 붙여 다시 읽어 돌려준다
    return await load_slot(session, trade_date, time_slot)


# 슬롯 하나 조회 (없으면 None)
async def load_slot(session: AsyncSession, trade_date: date, time_slot: str) -> TimelineSlot | None:
    return await session.scalar(select(TimelineSlot).where(TimelineSlot.trade_date == trade_date, TimelineSlot.time_slot == time_slot).options(*_EAGER_LOAD))


# 하루치 슬롯을 시간순으로 조회 ("07:30" 문자열 정렬이 곧 시간순이다)
async def load_day(session: AsyncSession, trade_date: date) -> list[TimelineSlot]:
    result = await session.scalars(select(TimelineSlot).where(TimelineSlot.trade_date == trade_date).order_by(TimelineSlot.time_slot).options(*_EAGER_LOAD))
    return list(result)
