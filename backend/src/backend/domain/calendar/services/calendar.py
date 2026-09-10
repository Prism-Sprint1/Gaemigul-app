# calendar.py
# FRED API 호출 -> 한국시간/한국어 변환 -> Supabase calendar_events 저장/조회
#
# ORM 모델을 쓰지 않는다 - 이 프로젝트에 Calendar용 SQLAlchemy ORM 모델 선례가 없어서, 새 패턴을
# 도입하는 대신 core/database.py의 async_session을 그대로 재사용해 raw SQL(sqlalchemy.text)로
# calendar_events 테이블에 접근하기로 팀에서 결정했다(2026-09-10).

from __future__ import annotations

from datetime import datetime
from datetime import time as dt_time
from zoneinfo import ZoneInfo

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core import fred_client
from backend.core.database import async_session
from backend.domain.calendar.schemas.calendar import CalendarEvent

_US_EASTERN = ZoneInfo("America/New_York")
_KST = ZoneInfo("Asia/Seoul")

# 카테고리별 공식 발표 고정 시각(미국 동부시간). FRED는 발표 "날짜"만 주고 "시각"은 안 주기 때문에,
# 기관이 공개적으로 고정해둔 발표 시각(예: BLS의 CPI는 항상 08:30 ET)을 사용해 KST로 정확히 환산한다.
# market_hours.py의 장 운영시간표와 같은 성격의 공개된 사실이며, 임의로 추정한 값이 아니다.
# 시각이 확인되지 않은 카테고리는 이 표에 넣지 않는다 - 그러면 time=None으로 처리된다.
_RELEASE_TIME_ET: dict[str, dt_time] = {
    "CPI": dt_time(8, 30),
}

_TITLES: dict[str, str] = {
    "CPI": "미국 소비자물가지수(CPI)",
}

_SUMMARIES: dict[str, str] = {
    "CPI": (
        "미국 소비자물가지수(CPI)는 미국에서 소비자가 구입하는 상품과 서비스의 가격 변화를 보여주는 "
        "대표적인 물가 지표입니다. 물가가 예상보다 높게 나오면 인플레이션 우려가 커지고 미국의 금리 "
        "인하 기대가 약해질 수 있어 주식시장에 부담으로 작용할 수 있습니다."
    ),
}

# summary 맨 앞에 "OOOO년 O월 OO 자료입니다."를 붙일 때 쓰는, "미국" 없는 지표 이름
_PERIOD_LABELS: dict[str, str] = {
    "CPI": "소비자물가지수(CPI)",
}


# FRED observation_date("2026-07-01")를 "2026년 7월" 형태로 변환.
# CPI의 observation_date는 "그 값이 설명하는 대상 기간"이지 발표일이 아니다 - title/summary에
# 이 대상 기간을 명시해서, publishedAt(발표일)과 헷갈리지 않도록 한다.
def _format_period_kr(observation_date: str) -> str:
    year, month, _ = observation_date.split("-")
    return f"{int(year)}년 {int(month)}월"


# 발표일(미국 기준 날짜)을 KST 날짜/시각으로 변환. 고정 발표시각을 모르는 카테고리는 (날짜, None) 반환
def _to_kst(release_date: str, category: str) -> tuple[str, str | None]:
    release_time = _RELEASE_TIME_ET.get(category)
    if release_time is None:
        return release_date, None

    naive_date = datetime.strptime(release_date, "%Y-%m-%d").date()
    et_dt = datetime.combine(naive_date, release_time, tzinfo=_US_EASTERN)
    kst_dt = et_dt.astimezone(_KST)
    return kst_dt.strftime("%Y-%m-%d"), kst_dt.strftime("%H:%M")


# FRED observation 값 정리. "."은 값 없음을 의미하므로 None으로 바꾼다
def _clean_value(raw: str | None) -> str | None:
    if raw is None or raw == ".":
        return None
    return raw


# FRED에서 CPI(CPIAUCSL)를 1회 가져와 Supabase calendar_events에 저장한다.
# main.py 스케줄러에는 아직 연결하지 않는다 - scripts/seed_cpi.py로 수동 실행한다.
async def ingest_cpi_from_fred() -> CalendarEvent:
    series_id = "CPIAUCSL"
    category = "CPI"

    observations = fred_client.get_series_observations(series_id, limit=2)
    latest = observations[0]
    previous = observations[1] if len(observations) > 1 else None

    release_id = fred_client.get_series_release_id(series_id)
    release_dates = fred_client.get_release_dates(release_id, limit=1)
    # 실제 발표일 조회에 실패하면 관측일(observation date)로 대체 - 최소한 임의 날짜를 만들지는 않는다
    release_date = release_dates[0]["date"] if release_dates else latest["date"]

    published_at, released_time = _to_kst(release_date, category)
    actual = _clean_value(latest["value"])
    period_kr = _format_period_kr(latest["date"])

    event = CalendarEvent(
        id=f"fred-{series_id}-{latest['date']}",
        publishedAt=published_at,
        time=released_time,
        region="미국",
        category=category,
        title=f"{_TITLES[category]} - {period_kr}",
        summary=f"{period_kr} {_PERIOD_LABELS[category]} 자료입니다. {_SUMMARIES[category]}",
        previous=_clean_value(previous["value"]) if previous else None,
        actual=actual,
        status="SCHEDULED" if actual is None else "RELEASED",
    )

    async with async_session() as session:
        await _upsert_event(session, event)
        await session.commit()

    return event


# calendar_events에 upsert - id가 이미 있으면 UPDATE, 없으면 INSERT (36번 항목: 중복 방지)
async def _upsert_event(session: AsyncSession, event: CalendarEvent) -> None:
    await session.execute(
        text(
            """
            INSERT INTO calendar_events
                (id, "publishedAt", start_date, end_date, "time", region, category,
                 title, summary, importance, previous, forecast, actual, status)
            VALUES
                (:id, :publishedAt, :start_date, :end_date, :time, :region, :category,
                 :title, :summary, :importance, :previous, :forecast, :actual, :status)
            ON CONFLICT (id) DO UPDATE SET
                "publishedAt" = EXCLUDED."publishedAt",
                start_date = EXCLUDED.start_date,
                end_date = EXCLUDED.end_date,
                "time" = EXCLUDED."time",
                region = EXCLUDED.region,
                category = EXCLUDED.category,
                title = EXCLUDED.title,
                summary = EXCLUDED.summary,
                importance = EXCLUDED.importance,
                previous = EXCLUDED.previous,
                forecast = EXCLUDED.forecast,
                actual = EXCLUDED.actual,
                status = EXCLUDED.status
            """
        ),
        event.model_dump(),
    )


# 해당 연/월에 publishedAt(KST 기준)이 속하는 이벤트 목록을 조회.
# 문자열 앞부분 비교(LIKE)가 아니라 >= / < 범위 조건으로 조회한다.
async def get_events_by_month(session: AsyncSession, year: int, month: int) -> list[CalendarEvent]:
    start = f"{year:04d}-{month:02d}-01"
    end_year, end_month = (year + 1, 1) if month == 12 else (year, month + 1)
    end = f"{end_year:04d}-{end_month:02d}-01"

    result = await session.execute(
        text(
            """
            SELECT id, "publishedAt", start_date, end_date, "time", region, category,
                   title, summary, importance, previous, forecast, actual, status
            FROM calendar_events
            WHERE "publishedAt" >= :start AND "publishedAt" < :end
            ORDER BY "publishedAt" ASC, "time" ASC NULLS LAST
            """
        ),
        {"start": start, "end": end},
    )
    return [CalendarEvent(**row) for row in result.mappings().all()]
