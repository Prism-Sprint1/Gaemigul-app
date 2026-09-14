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

from backend.core import fred_client, kis_client
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
    # PPI도 CPI와 같은 발표 기관(BLS)이 같은 고정 시각(08:30 ET)에 발표한다 - 임의 추정 아님
    "PPI": dt_time(8, 30),
    # GDP는 BEA가 발표하며, BEA도 08:30 ET에 발표한다는 것이 공개된 사실이다 - 임의 추정 아님
    "GDP": dt_time(8, 30),
    # PAYEMS(비농업 고용)도 BLS가 08:30 ET에 발표한다 - 임의 추정 아님
    "PAYEMS": dt_time(8, 30),
    # UNRATE(실업률)는 PAYEMS와 같은 보고서(Employment Situation)라 같은 기관·시각
    "UNRATE": dt_time(8, 30),
    # PCE도 BEA가 발표하며(GDP와 같은 release 계열), BEA도 08:30 ET에 발표한다
    "PCE": dt_time(8, 30),
}

_TITLES: dict[str, str] = {
    "CPI": "미국 소비자물가지수(CPI)",
    "PPI": "미국 생산자물가지수(PPI)",
    "GDP": "미국 국내총생산(GDP)",
    "PAYEMS": "미국 비농업 고용(Nonfarm Payrolls)",
    "UNRATE": "미국 실업률",
    "PCE": "미국 개인소비지출 물가지수(PCE)",
}

_SUMMARIES: dict[str, str] = {
    "CPI": (
        "미국 소비자물가지수(CPI)는 미국에서 소비자가 구입하는 상품과 서비스의 가격 변화를 보여주는 "
        "대표적인 물가 지표입니다. 물가가 예상보다 높게 나오면 인플레이션 우려가 커지고 미국의 금리 "
        "인하 기대가 약해질 수 있어 주식시장에 부담으로 작용할 수 있습니다."
    ),
    "PPI": (
        "미국 생산자물가지수(PPI)는 기업이 상품과 서비스를 생산하면서 받는 가격의 변화를 보여주는 "
        "지표입니다. 생산 단계의 물가 흐름을 확인할 수 있어 향후 소비자물가와 인플레이션 흐름을 "
        "판단할 때 참고합니다."
    ),
    "GDP": (
        "미국 국내총생산(GDP)은 미국 경제가 얼마나 성장하고 있는지를 보여주는 대표적인 경제지표입니다. "
        "예상보다 경제성장이 강하면 경기 회복 신호가 될 수 있지만 미국 금리 인하 기대에는 영향을 줄 수 "
        "있습니다."
    ),
    "PAYEMS": (
        "미국 비농업 고용(Nonfarm Payrolls)은 농업을 제외한 미국 기업과 정부에서 한 달 동안 늘어나거나 "
        "줄어든 일자리 수를 보여주는 대표적인 고용 지표입니다. 고용이 예상보다 크게 늘면 경기가 튼튼하다는 "
        "신호가 될 수 있지만, 동시에 물가 상승 압력을 키워 미국의 금리 인하 기대를 약화시킬 수 있어 "
        "주식시장에 영향을 줄 수 있습니다."
    ),
    "UNRATE": (
        "미국 실업률은 일할 의사가 있는 노동인구 중 실제로 일자리가 없는 사람의 비율을 보여주는 대표적인 "
        "고용 지표입니다. 실업률이 예상보다 낮으면 고용시장이 탄탄하다는 신호지만, 동시에 물가 상승 압력을 "
        "키워 금리 인하 기대를 약화시킬 수 있고, 반대로 예상보다 높으면 경기 둔화 우려로 이어질 수 있어 "
        "주식시장에 영향을 줄 수 있습니다."
    ),
    "PCE": (
        "미국 개인소비지출(PCE) 물가지수는 소비자들이 실제로 구매한 상품과 서비스의 가격 변화를 반영하는 "
        "물가 지표로, 연방준비제도(연준)가 통화정책을 결정할 때 CPI보다 더 공식적으로 참고하는 지표입니다. "
        "PCE 물가가 예상보다 높게 나오면 인플레이션 우려가 커지고 금리 인하 기대가 약해질 수 있어 "
        "주식시장에 부담으로 작용할 수 있습니다."
    ),
}

# summary 맨 앞에 "OOOO년 O월/O분기 OO 자료입니다."를 붙일 때 쓰는, "미국" 없는 지표 이름
_PERIOD_LABELS: dict[str, str] = {
    "CPI": "소비자물가지수(CPI)",
    "PPI": "생산자물가지수(PPI)",
    "GDP": "국내총생산(GDP)",
    "PAYEMS": "비농업 고용",
    "UNRATE": "실업률",
    "PCE": "개인소비지출(PCE) 물가지수",
}

# 카테고리별 FRED series_id
_SERIES_IDS: dict[str, str] = {
    "CPI": "CPIAUCSL",
    "PPI": "PPIACO",
    "GDP": "GDP",
    "PAYEMS": "PAYEMS",
    "UNRATE": "UNRATE",
    "PCE": "PCEPI",
}

# 지표(indicator) -> 캘린더에 실제로 저장할 category(5개 색상 대분류) 매핑.
# "CPI"/"PPI"/"GDP"는 코드 내부에서 FRED series/제목/발표시각 등을 찾는 키(indicator)로만 쓰고,
# DB에는 이 표로 변환한 5개 고정값(macro/rate/dividend/earnings/optionExpiry)만 저장한다
# (IMPLEMENTATION_LOG.md 14번 항목 결정 사항).
_CATEGORY_OF: dict[str, str] = {
    "CPI": "macro",
    "PPI": "macro",
    "GDP": "macro",
    "PAYEMS": "macro",
    "UNRATE": "macro",
    "PCE": "macro",
}

# 지표별 발표 주기. GDP는 분기별이라 CPI/PPI(월별)와 다르게 처리해야 한다 - 월별 12개로
# 임의 생성하면 안 된다(원래 CLAUDE.md 원칙). 표에 없으면 monthly로 취급.
_FREQUENCY: dict[str, str] = {
    "GDP": "quarterly",
}


# FRED observation_date("2026-07-01")를 "2026년 7월"(월별) 또는 "2026년 3분기"(분기별)로 변환.
# observation_date는 "그 값이 설명하는 대상 기간"이지 발표일이 아니다 - title/summary에 이 대상
# 기간을 명시해서, publishedAt(발표일)과 헷갈리지 않도록 한다.
def _format_period_kr(observation_date: str, indicator: str) -> str:
    year, month, _ = observation_date.split("-")
    year, month = int(year), int(month)
    if _FREQUENCY.get(indicator) == "quarterly":
        quarter = (month - 1) // 3 + 1
        return f"{year}년 {quarter}분기"
    return f"{year}년 {month}월"


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


# FRED에서 지정한 지표(indicator: "CPI"/"PPI")의 최신 데이터를 1회 가져와
# Supabase calendar_events에 저장한다. indicator는 코드 내부에서만 쓰는 세부 식별자이고,
# 실제 DB에 저장되는 category는 _CATEGORY_OF로 변환한 5개 고정값이다.
# main.py 스케줄러에는 아직 연결하지 않는다 - scripts/seed_cpi.py, scripts/seed_ppi.py로 수동 실행한다.
async def _ingest_from_fred(indicator: str) -> CalendarEvent:
    series_id = _SERIES_IDS[indicator]

    observations = fred_client.get_series_observations(series_id, limit=2)
    latest = observations[0]
    previous = observations[1] if len(observations) > 1 else None

    release_id = fred_client.get_series_release_id(series_id)
    release_dates = fred_client.get_release_dates(release_id, limit=1)
    # 실제 발표일 조회에 실패하면 관측일(observation date)로 대체 - 최소한 임의 날짜를 만들지는 않는다
    release_date = release_dates[0]["date"] if release_dates else latest["date"]

    published_at, released_time = _to_kst(release_date, indicator)
    actual = _clean_value(latest["value"])
    period_kr = _format_period_kr(latest["date"], indicator)

    event = CalendarEvent(
        id=f"fred-{series_id}-{latest['date']}",
        publishedAt=published_at,
        time=released_time,
        region="미국",
        category=_CATEGORY_OF[indicator],
        title=f"{_TITLES[indicator]} - {period_kr}",
        summary=f"{period_kr} {_PERIOD_LABELS[indicator]} 자료입니다. {_SUMMARIES[indicator]}",
        previous=_clean_value(previous["value"]) if previous else None,
        actual=actual,
        status="SCHEDULED" if actual is None else "RELEASED",
    )

    async with async_session() as session:
        await _upsert_event(session, event)
        await session.commit()

    return event


# FRED에서 지정한 지표(indicator)의 특정 연도(1~12월) 전체를 한 번에 가져와 upsert한다.
# - 이미 발표된 달: 실제 관측값으로 RELEASED
# - 아직 발표 안 된 달: FRED release calendar에 예정 발표일이 있는 경우에만 SCHEDULED(actual=null)
#   생성. 예정 발표일 자체가 FRED에 없는 달은 만들지 않는다(임의 날짜 생성 금지).
# - previous는 그 시점까지 실제로 존재하는 가장 최근 관측값(과거 실측치이므로 임의 생성 아님)
async def ingest_year_from_fred(indicator: str, year: int) -> list[CalendarEvent]:
    series_id = _SERIES_IDS[indicator]
    quarterly = _FREQUENCY.get(indicator) == "quarterly"
    # 분기별이면 대상 기간의 첫 달이 1/4/7/10월뿐이다 - 나머지 달로 임의 생성하지 않는다
    period_months = (1, 4, 7, 10) if quarterly else range(1, 13)
    step = 3 if quarterly else 1

    # 1월(또는 1분기)의 previous 계산을 위해 전년도분까지 같이 가져온다
    observations = fred_client.get_series_observations(
        series_id,
        sort_order="asc",
        limit=100,
        observation_start=f"{year - 1}-01-01",
        observation_end=f"{year}-12-31",
    )
    obs_by_date: dict[str, str] = {o["date"]: o["value"] for o in observations}
    known_dates = sorted(obs_by_date)

    release_id = fred_client.get_series_release_id(series_id)
    # 마지막 기간분 발표일은 보통 다음 해 초에 나오므로 조회 범위를 다음 해 2월까지 넉넉히 잡는다
    release_dates = fred_client.get_release_dates(
        release_id,
        sort_order="asc",
        limit=100,
        realtime_start=f"{year}-01-01",
        realtime_end=f"{year + 1}-02-28",
        include_release_dates_with_no_data=True,
    )
    release_date_strs = [d["date"] for d in release_dates]

    events: list[CalendarEvent] = []
    for month in period_months:
        obs_date = f"{year}-{month:02d}-01"
        next_month = month + step
        next_month_year = year
        if next_month > 12:
            next_month -= 12
            next_month_year += 1
        next_month_first = f"{next_month_year}-{next_month:02d}-01"

        # 다음 기간 1일 이후 발표일 후보들. GDP처럼 한 기간에 발표가 여러 번(속보/잠정/확정)
        # 있는 지표는 이 중 첫 후보가 실제로는 다른 기간(예: 직전 분기 확정치)의 발표일일 수 있어서
        # 후보 하나로 단정하지 않는다 - 실제 라이브 호출로 발견한 문제.
        candidates = [d for d in release_date_strs if d >= next_month_first]
        if not candidates:
            # FRED release calendar에 이 기간의 예정 발표일 자체가 없음 - 임의로 만들지 않고 건너뜀
            continue

        raw_value = obs_by_date.get(obs_date)
        actual = _clean_value(raw_value) if raw_value is not None else None

        if actual is not None:
            # 이미 발표된 값이면, 그 값이 실제로 처음 등장한 날짜를 후보들 중에서 라이브로 확인한다
            # (realtime_start/end를 그 날짜로 고정해서 그 시점 스냅샷에 값이 있는지 직접 확인)
            release_date = candidates[0]
            for candidate in candidates:
                pinned = fred_client.get_series_observations(
                    series_id,
                    observation_start=obs_date,
                    observation_end=obs_date,
                    realtime_start=candidate,
                    realtime_end=candidate,
                )
                if pinned and _clean_value(pinned[0]["value"]) is not None:
                    release_date = candidate
                    break
        else:
            # 아직 발표 안 된 기간의 예정일은 후보 중 가장 이른 날짜(=최초/속보 발표일)로 본다
            release_date = candidates[0]

        prev_dates = [d for d in known_dates if d < obs_date]
        previous = _clean_value(obs_by_date[prev_dates[-1]]) if prev_dates else None

        published_at, released_time = _to_kst(release_date, indicator)
        period_kr = _format_period_kr(obs_date, indicator)

        event = CalendarEvent(
            id=f"fred-{series_id}-{obs_date}",
            publishedAt=published_at,
            time=released_time,
            region="미국",
            category=_CATEGORY_OF[indicator],
            title=f"{_TITLES[indicator]} - {period_kr}",
            summary=f"{period_kr} {_PERIOD_LABELS[indicator]} 자료입니다. {_SUMMARIES[indicator]}",
            previous=previous,
            actual=actual,
            status="SCHEDULED" if actual is None else "RELEASED",
        )
        events.append(event)

    async with async_session() as session:
        for event in events:
            await _upsert_event(session, event)
        await session.commit()

    return events


# 기존 호출부(scripts/seed_cpi.py 등)와의 호환을 위한 얇은 래퍼 - 동작은 이전과 동일
async def ingest_cpi_from_fred() -> CalendarEvent:
    return await _ingest_from_fred("CPI")


async def ingest_ppi_from_fred() -> CalendarEvent:
    return await _ingest_from_fred("PPI")


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


# ---------------------------------------------------------------------------
# KIS(한국투자증권) 예탁원정보(배당일정) 연동
# FRED 지표와 달리 "수치 발표"가 아니라 "배당기준일이라는 사실" 자체가 중요한 이벤트라, previous/
# forecast 개념이 없다. region은 국가만 쓰고 회사명은 title에 넣는다(2026-09-14 결정 사항).
# ---------------------------------------------------------------------------


# KIS 응답값 정리. 일부 숫자 필드는 고정폭이라 앞에 공백이 붙어서 오므로 먼저 trim한다
# (예: fix_subscr_pri="       18000" - 실제 라이브 응답으로 확인한 버그, summary/actual에
# 그대로 공백이 새어나가고 있었음). trim 후 ""(빈 문자열) 또는 "0"/"0.00"은 아직 금액이
# 확정 안 됐다는 뜻이라 None으로 바꾼다(FRED의 "."과 같은 역할, KIS는 표현 방식이 다름)
def _clean_kis_value(raw: str | None) -> str | None:
    if raw is None:
        return None
    trimmed = raw.strip()
    if trimmed in ("", "0", "0.00"):
        return None
    return trimmed


# KIS 날짜 형식 "YYYY/MM/DD" -> "YYYY-MM-DD". 빈 문자열이면 None
def _clean_kis_date(raw: str | None) -> str | None:
    if not raw or not raw.strip():
        return None
    return raw.strip().replace("/", "-")


# KIS ksdinfo/dividend 레코드 1건을 CalendarEvent로 변환. record_date가 없으면 None 반환
def _dividend_event_from_kis(record: dict, today_kst: str) -> CalendarEvent | None:
    record_date_raw = record.get("record_date")
    if not record_date_raw or len(record_date_raw) != 8:
        return None
    published_at = f"{record_date_raw[0:4]}-{record_date_raw[4:6]}-{record_date_raw[6:8]}"

    sht_cd = record.get("sht_cd", "")
    isin_name = (record.get("isin_name") or "").strip()
    divi_kind = (record.get("divi_kind") or "").strip()
    per_sto_divi_amt = _clean_kis_value(record.get("per_sto_divi_amt"))
    divi_pay_dt = _clean_kis_date(record.get("divi_pay_dt"))

    kind_label = f"({divi_kind})" if divi_kind else ""
    title = f"{isin_name} 배당기준일{kind_label}".strip()

    summary_parts = [f"{isin_name}의 배당기준일입니다."]
    if per_sto_divi_amt:
        summary_parts.append(f"주당 {per_sto_divi_amt}원 배당 예정입니다.")
    else:
        summary_parts.append("배당금액은 아직 확정되지 않았습니다.")
    if divi_pay_dt:
        summary_parts.append(f"지급 예정일은 {divi_pay_dt}입니다.")

    return CalendarEvent(
        id=f"kis-dividend-{sht_cd}-{record_date_raw}",
        publishedAt=published_at,
        time=None,
        region="한국",
        category="dividend",
        title=title,
        summary=" ".join(summary_parts),
        previous=None,
        actual=per_sto_divi_amt,
        status="SCHEDULED" if published_at >= today_kst else "RELEASED",
    )


# 지정한 종목코드 목록의 배당일정을 KIS에서 가져와 Supabase calendar_events에 upsert한다.
# 종목코드를 하나씩 지정해서 조회하므로(sht_cd), 전체조회 시 발생하는 100건 페이지 제한 문제가 없다.
async def ingest_dividends_from_kis(stock_codes: list[str], f_dt: str, t_dt: str) -> list[CalendarEvent]:
    today_kst = datetime.now(_KST).strftime("%Y-%m-%d")

    events: list[CalendarEvent] = []
    for sht_cd in stock_codes:
        records = kis_client.get_dividend_schedule(f_dt, t_dt, sht_cd=sht_cd)
        for record in records:
            event = _dividend_event_from_kis(record, today_kst)
            if event is not None:
                events.append(event)

    async with async_session() as session:
        for event in events:
            await _upsert_event(session, event)
        await session.commit()

    return events


# ---------------------------------------------------------------------------
# KIS(한국투자증권) 예탁원정보(합병_분할일정) 연동
# ---------------------------------------------------------------------------


# KIS 날짜 형식 "YYYYMMDD"(구분자 없음) -> "YYYY-MM-DD". 빈 문자열이면 None
def _clean_kis_date_compact(raw: str | None) -> str | None:
    if not raw:
        return None
    trimmed = raw.strip()
    if len(trimmed) != 8:
        return None
    return f"{trimmed[0:4]}-{trimmed[4:6]}-{trimmed[6:8]}"


# KIS 기간 형식 "YYYY/MM/DD ~ YYYY/MM/DD" 또는 "YYYY/MM/DD ~"(종료일 미정)를
# (시작일, 종료일) 튜플로 분리한다. 둘 다 "YYYY-MM-DD" 형식, 없으면 None
def _split_kis_date_range(raw: str | None) -> tuple[str | None, str | None]:
    if not raw:
        return None, None
    parts = [p.strip() for p in raw.split("~")]
    start = _clean_kis_date(parts[0]) if parts and parts[0] else None
    end = _clean_kis_date(parts[1]) if len(parts) > 1 and parts[1] else None
    return start, end


# KIS ksdinfo/merger-split 레코드 1건을 CalendarEvent로 변환. record_date가 없으면 None 반환.
# 매매정지 기간(td_stop_dt)이 있으면 start_date/end_date를 실제로 채운다 - 이 두 컬럼이 원래
# "다일 이벤트"용으로 예비돼 있었는데(CLAUDE.md), 여기서 처음 실사용하는 것이다.
def _merger_split_event_from_kis(record: dict, today_kst: str) -> CalendarEvent | None:
    record_date_raw = record.get("record_date")
    if not record_date_raw or len(record_date_raw) != 8:
        return None
    published_at = f"{record_date_raw[0:4]}-{record_date_raw[4:6]}-{record_date_raw[6:8]}"

    sht_cd = record.get("sht_cd", "")
    seq = record.get("seq") or "0"
    cust_nm = (record.get("cust_nm") or "").strip()
    opp_cust_nm = (record.get("opp_cust_nm") or "").strip()
    merge_type = (record.get("merge_type") or "").strip()
    merge_rate = _clean_kis_value(record.get("merge_rate"))
    start_date, end_date = _split_kis_date_range(record.get("td_stop_dt"))
    list_dt = _clean_kis_date_compact(record.get("list_dt"))

    title = f"{cust_nm} {merge_type}".strip()

    summary_parts = [f"{cust_nm}의 {merge_type} 절차가 진행됩니다."]
    if opp_cust_nm:
        summary_parts.append(f"관련 회사: {opp_cust_nm}.")
    if merge_rate:
        summary_parts.append(f"비율: {merge_rate}.")
    if start_date:
        period_text = f"{start_date}부터" + (f" {end_date}까지" if end_date else "")
        summary_parts.append(f"매매정지 기간: {period_text}.")
    if list_dt:
        summary_parts.append(f"신주 상장(예정)일: {list_dt}.")

    return CalendarEvent(
        id=f"kis-mergersplit-{sht_cd}-{record_date_raw}-{seq}",
        publishedAt=published_at,
        start_date=start_date,
        end_date=end_date,
        time=None,
        region="한국",
        category="macro",
        title=title,
        summary=" ".join(summary_parts),
        previous=None,
        actual=merge_rate,
        status="SCHEDULED" if published_at >= today_kst else "RELEASED",
    )


# KIS 예탁원정보(합병_분할일정)에서 전체 시장의 합병/분할 일정을 가져와 upsert한다.
# 배당일정과 달리 연간 건수가 적어서(30건 안팎) 종목코드 없이 전체 조회 한 번으로 충분하다.
async def ingest_merger_splits_from_kis(f_dt: str, t_dt: str) -> list[CalendarEvent]:
    today_kst = datetime.now(_KST).strftime("%Y-%m-%d")

    records = kis_client.get_merger_split_schedule(f_dt, t_dt)
    events = [
        event
        for record in records
        if (event := _merger_split_event_from_kis(record, today_kst)) is not None
    ]

    async with async_session() as session:
        for event in events:
            await _upsert_event(session, event)
        await session.commit()

    return events


# ---------------------------------------------------------------------------
# KIS(한국투자증권) 신규상장(IPO)/유상증자/무상증자 연동
# 셋 다 category="macro"로 저장한다 - 5개 고정 카테고리 중 합병/분할과 성격이 비슷한
# "기업 주식구조 변경" 이벤트라 같은 분류로 묶었다(14번 항목에서 합병/분할을 macro로 정한 것과
# 동일한 판단 기준 적용, 확정된 지침은 아니라 향후 조정 가능).
# ---------------------------------------------------------------------------


# KIS ksdinfo/pub-offer(공모주청약일정=IPO) 레코드 1건을 CalendarEvent로 변환
def _ipo_event_from_kis(record: dict, today_kst: str) -> CalendarEvent | None:
    record_date_raw = record.get("record_date")
    if not record_date_raw or len(record_date_raw) != 8:
        return None
    published_at = f"{record_date_raw[0:4]}-{record_date_raw[4:6]}-{record_date_raw[6:8]}"

    sht_cd = record.get("sht_cd", "")
    isin_name = (record.get("isin_name") or "").strip()
    fix_subscr_pri = _clean_kis_value(record.get("fix_subscr_pri"))
    lead_mgr = (record.get("lead_mgr") or "").strip()
    start_date, end_date = _split_kis_date_range(record.get("subscr_dt"))
    list_dt = _clean_kis_date_compact(record.get("list_dt"))

    title = f"{isin_name} 공모주 청약"

    summary_parts = [f"{isin_name} 공모주 청약 일정입니다."]
    if fix_subscr_pri:
        summary_parts.append(f"공모가는 {fix_subscr_pri}원입니다.")
    if lead_mgr:
        summary_parts.append(f"주간사: {lead_mgr}.")
    if list_dt:
        summary_parts.append(f"상장(예정)일: {list_dt}.")

    return CalendarEvent(
        id=f"kis-ipo-{sht_cd}-{record_date_raw}",
        publishedAt=published_at,
        start_date=start_date,
        end_date=end_date,
        time=None,
        region="한국",
        category="macro",
        title=title,
        summary=" ".join(summary_parts),
        previous=None,
        actual=fix_subscr_pri,
        status="SCHEDULED" if published_at >= today_kst else "RELEASED",
    )


# KIS 예탁원정보(공모주청약일정)에서 전체 시장의 IPO 일정을 가져와 upsert한다
async def ingest_ipos_from_kis(f_dt: str, t_dt: str) -> list[CalendarEvent]:
    today_kst = datetime.now(_KST).strftime("%Y-%m-%d")

    records = kis_client.get_ipo_schedule(f_dt, t_dt)
    events = [
        event for record in records if (event := _ipo_event_from_kis(record, today_kst)) is not None
    ]

    async with async_session() as session:
        for event in events:
            await _upsert_event(session, event)
        await session.commit()

    return events


# KIS ksdinfo/paidin-capin(유상증자일정) 레코드 1건을 CalendarEvent로 변환
def _paidin_capital_increase_event_from_kis(record: dict, today_kst: str) -> CalendarEvent | None:
    record_date_raw = record.get("record_date")
    if not record_date_raw or len(record_date_raw) != 8:
        return None
    published_at = f"{record_date_raw[0:4]}-{record_date_raw[4:6]}-{record_date_raw[6:8]}"

    sht_cd = record.get("sht_cd", "")
    isin_name = (record.get("isin_name") or "").strip()
    fix_rate = _clean_kis_value(record.get("fix_rate"))
    fix_price = _clean_kis_value(record.get("fix_price"))
    start_date, end_date = _split_kis_date_range(record.get("sub_term"))
    right_dt = _clean_kis_date_compact(record.get("right_dt"))

    title = f"{isin_name} 유상증자"

    summary_parts = [f"{isin_name}의 유상증자가 진행됩니다."]
    if fix_rate:
        summary_parts.append(f"신주배정비율: {fix_rate}%.")
    if fix_price:
        summary_parts.append(f"확정 발행가: {fix_price}원.")
    if right_dt:
        summary_parts.append(f"권리락일: {right_dt}.")

    return CalendarEvent(
        id=f"kis-paidincap-{sht_cd}-{record_date_raw}",
        publishedAt=published_at,
        start_date=start_date,
        end_date=end_date,
        time=None,
        region="한국",
        category="macro",
        title=title,
        summary=" ".join(summary_parts),
        previous=None,
        actual=fix_rate,
        status="SCHEDULED" if published_at >= today_kst else "RELEASED",
    )


# KIS 예탁원정보(유상증자일정)에서 전체 시장의 유상증자 일정을 가져와 upsert한다
async def ingest_paidin_capital_increases_from_kis(f_dt: str, t_dt: str) -> list[CalendarEvent]:
    today_kst = datetime.now(_KST).strftime("%Y-%m-%d")

    records = kis_client.get_paidin_capital_increase_schedule(f_dt, t_dt)
    events = [
        event
        for record in records
        if (event := _paidin_capital_increase_event_from_kis(record, today_kst)) is not None
    ]

    async with async_session() as session:
        for event in events:
            await _upsert_event(session, event)
        await session.commit()

    return events


# KIS ksdinfo/bonus-issue(무상증자일정) 레코드 1건을 CalendarEvent로 변환
def _bonus_issue_event_from_kis(record: dict, today_kst: str) -> CalendarEvent | None:
    record_date_raw = record.get("record_date")
    if not record_date_raw or len(record_date_raw) != 8:
        return None
    published_at = f"{record_date_raw[0:4]}-{record_date_raw[4:6]}-{record_date_raw[6:8]}"

    sht_cd = record.get("sht_cd", "")
    isin_name = (record.get("isin_name") or "").strip()
    fix_rate = _clean_kis_value(record.get("fix_rate"))
    right_dt = _clean_kis_date_compact(record.get("right_dt"))

    title = f"{isin_name} 무상증자"

    summary_parts = [f"{isin_name}의 무상증자가 진행됩니다."]
    if fix_rate:
        summary_parts.append(f"신주배정비율: {fix_rate}%.")
    if right_dt:
        summary_parts.append(f"권리락일: {right_dt}.")

    return CalendarEvent(
        id=f"kis-bonusissue-{sht_cd}-{record_date_raw}",
        publishedAt=published_at,
        time=None,
        region="한국",
        category="macro",
        title=title,
        summary=" ".join(summary_parts),
        previous=None,
        actual=fix_rate,
        status="SCHEDULED" if published_at >= today_kst else "RELEASED",
    )


# KIS 예탁원정보(무상증자일정)에서 지정한 종목코드들의 무상증자 일정을 가져와 upsert한다.
# 전체 시장 조회는 페이지 제한(100건)에 걸릴 수 있어 종목코드를 지정해서 쓴다(배당일정과 동일한 이유).
async def ingest_bonus_issues_from_kis(stock_codes: list[str], f_dt: str, t_dt: str) -> list[CalendarEvent]:
    today_kst = datetime.now(_KST).strftime("%Y-%m-%d")

    events: list[CalendarEvent] = []
    for sht_cd in stock_codes:
        records = kis_client.get_bonus_issue_schedule(f_dt, t_dt, sht_cd=sht_cd)
        for record in records:
            event = _bonus_issue_event_from_kis(record, today_kst)
            if event is not None:
                events.append(event)

    async with async_session() as session:
        for event in events:
            await _upsert_event(session, event)
        await session.commit()

    return events
