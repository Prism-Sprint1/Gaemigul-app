# timeline_repository.py
# 타임라인 슬롯을 DB에 넣고 꺼내는 코드
#
# 조립(timeline_service)과 저장(여기)을 나눈 이유: 수집·가공 로직과 DB 접근이 한 파일에 섞이면
# 나중에 "저장 방식만 바꾸고 싶을 때" 건드릴 범위가 넓어진다.
#
# 비동기 ORM에서 주의할 점
#   조회할 때 selectinload로 자식 테이블을 미리 같이 읽어와야 한다. 동기 ORM처럼 나중에
#   slot.news를 꺼내려 하면 MissingGreenlet 에러가 난다(비동기에서는 뒤늦은 조회가 안 됨).

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


# 시각을 한국 시간 시계값으로 바꾼다 (DB에는 시간대 정보 없이 저장한다 - models/timeline.py 참고)
def _to_naive_kst(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.astimezone(_KST).replace(tzinfo=None)


# 조회할 때 같이 읽어올 자식 테이블 목록
# 테이블을 추가하면 여기에도 넣어야 한다. 빠뜨리면 그 값만 조용히 비어 보인다
_EAGER_LOAD = (
    selectinload(TimelineSlot.insights),
    selectinload(TimelineSlot.beginner_guides),
    selectinload(TimelineSlot.news),
    selectinload(TimelineSlot.indicators),
    selectinload(TimelineSlot.intraday_changes),
    selectinload(TimelineSlot.leading_sectors).selectinload(TimelineLeadingSector.stocks),
    selectinload(TimelineSlot.top_gainers),
)


# 슬롯 하나를 저장한다. 같은 날 같은 시간대가 이미 있으면 지우고 새로 넣는다
#
# 덮어쓰기로 만든 이유: trade_date + time_slot에 유니크 제약이 걸려 있어서 그냥 INSERT하면
# 두 번째 실행부터 에러가 난다. 테스트로 여러 번 돌릴 때, 수집이 실패해서 다시 돌릴 때,
# 서버를 재시작했을 때 모두 재실행이 필요하다.
# 자식 테이블은 cascade가 걸려 있어서 슬롯 한 줄만 지우면 딸린 행이 전부 같이 지워진다
#
# collected: timeline_service가 모아둔 값 (브리핑/불개미/뉴스/지표/주도섹터)
async def save_slot(session: AsyncSession, trade_date: date, time_slot: str, collected: dict) -> TimelineSlot:
    existing = await session.scalar(
        select(TimelineSlot).where(TimelineSlot.trade_date == trade_date, TimelineSlot.time_slot == time_slot).options(*_EAGER_LOAD)
    )

    briefing = collected.get("briefing")
    guides = collected.get("beginner_guides", [])

    # LLM이 실패해서 브리핑이 비었는데 이미 저장된 브리핑이 있으면, 기존 것을 살려둔다
    #
    # 이 처리가 없으면 재실행이 위험해진다. 실제로 겪은 일인데, 브리핑이 잘 들어간 슬롯을
    # 지표 때문에 다시 수집했다가 그 순간 LLM 한도에 걸려서 멀쩡했던 브리핑이 빈 값으로 덮였다.
    # 새로 만든 게 없으면 기존 것을 유지하는 편이 항상 낫다
    if briefing is None and existing is not None and existing.briefing_headline:
        briefing = {
            "headline": existing.briefing_headline,
            "subtitle": existing.briefing_subtitle,
            "points": [{"seq": row.seq, "title": row.title, "body": row.body} for row in existing.insights],
        }
        print(f"[안내] {trade_date} {time_slot} - 새 브리핑이 없어서 기존 브리핑을 유지합니다.")

    if not guides and existing is not None and existing.beginner_guides:
        guides = [
            {"seq": row.seq, "title": row.title, "body": row.body, "tags": [tag.strip() for tag in (row.tags or "").split(",") if tag.strip()]}
            for row in existing.beginner_guides
        ]

    if existing is not None:
        await session.delete(existing)
        await session.flush()  # 새 행을 넣기 전에 삭제를 먼저 DB에 반영해야 유니크 제약에 안 걸린다
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
            # 태그는 쉼표로 이어붙여 한 칸에 저장한다 (모델 주석 참고)
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

    # 방금 넣은 행을 자식까지 붙여서 다시 읽어 돌려준다 (저장 결과를 바로 응답에 쓸 수 있게)
    return await load_slot(session, trade_date, time_slot)


# 슬롯 하나를 꺼낸다 (없으면 None)
async def load_slot(session: AsyncSession, trade_date: date, time_slot: str) -> TimelineSlot | None:
    return await session.scalar(select(TimelineSlot).where(TimelineSlot.trade_date == trade_date, TimelineSlot.time_slot == time_slot).options(*_EAGER_LOAD))


# 하루치 슬롯을 시간 순서대로 꺼낸다
# time_slot이 "07:30" 형태의 문자열이라 문자 정렬만으로 시간 순서가 맞는다(앞자리가 0으로 채워져 있어서)
async def load_day(session: AsyncSession, trade_date: date) -> list[TimelineSlot]:
    result = await session.scalars(select(TimelineSlot).where(TimelineSlot.trade_date == trade_date).order_by(TimelineSlot.time_slot).options(*_EAGER_LOAD))
    return list(result)
