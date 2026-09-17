# 원/달러 환율 차트 서비스.
# KIS 현재가를 30분마다 DB에 저장하고 오늘·5일은 실제 스냅샷, 월간은 KIS 일봉으로 구성한다.

import asyncio
import logging
from datetime import UTC, date, datetime, time, timedelta
from threading import Lock
from zoneinfo import ZoneInfo

from sqlalchemy import delete, select

from backend.core import kis_client
from backend.core.database import get_session_factory
from backend.domain.market.models.exchange_rate import ExchangeRateSnapshot
from backend.domain.market.schemas.exchange_rate import ExchangeRateResponse

logger = logging.getLogger(__name__)

_KST = ZoneInfo("Asia/Seoul")
_MARKET_DIV = "X"
_SYMBOL = "FX@KRW"
_POINT_COUNT = 8
_RETENTION_DAYS = 10
_cache: dict[str, dict] = {}
_lock = Lock()


def _number(row: dict, *keys: str) -> float | None:
    for key in keys:
        raw = row.get(key)
        if raw not in (None, ""):
            try:
                return float(str(raw).replace(",", ""))
            except ValueError:
                continue
    return None


def _floor_half_hour(now: datetime) -> datetime:
    return now.replace(minute=0 if now.minute < 30 else 30, second=0, microsecond=0)


def _evenly_spaced(points: list[tuple[datetime, float]], count: int = _POINT_COUNT) -> list[tuple[datetime, float]]:
    """시간순 실제 관측값을 유지하면서 전체 구간에서 최대 count개를 고른다."""
    if len(points) <= count:
        return points
    indices = [round(index * (len(points) - 1) / (count - 1)) for index in range(count)]
    return [points[index] for index in indices]


def _payload(
    period: str,
    points: list[tuple[datetime, float]],
    updated_at: datetime,
    *,
    is_complete: bool | None = None,
) -> dict:
    return {
        "period": period,
        # DB에는 한국시간 naive datetime으로 보관하지만 API에는 +09:00을 명시해 브라우저 시간대 해석 차이를 막는다.
        "points": [
            {
                "timestamp": timestamp.replace(tzinfo=_KST) if timestamp.tzinfo is None else timestamp,
                "value": round(value, 2),
            }
            for timestamp, value in points
        ],
        "requested_point_count": _POINT_COUNT,
        "is_complete": len(points) == _POINT_COUNT if is_complete is None else is_complete,
        "updated_at": updated_at,
    }


async def _save_snapshot(sampled_at: datetime, value: float) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        existing = await session.scalar(
            select(ExchangeRateSnapshot).where(ExchangeRateSnapshot.sampled_at == sampled_at)
        )
        if existing is None:
            session.add(
                ExchangeRateSnapshot(
                    sampled_at=sampled_at,
                    value=value,
                    created_at=datetime.now(_KST).replace(tzinfo=None),
                )
            )
        else:
            existing.value = value
        # 오늘·5일 차트에는 최근 5일만 필요하지만 장애·휴일 여유를 두고 10일을 보관한다.
        # 경계 시각은 보존하고 그보다 오래된 행만 같은 트랜잭션에서 지운다.
        await session.execute(
            delete(ExchangeRateSnapshot).where(
                ExchangeRateSnapshot.sampled_at < sampled_at - timedelta(days=_RETENTION_DAYS)
            )
        )
        await session.commit()


async def _snapshot_points(start: datetime) -> list[tuple[datetime, float]]:
    session_factory = get_session_factory()
    async with session_factory() as session:
        rows = (
            await session.scalars(
                select(ExchangeRateSnapshot)
                .where(ExchangeRateSnapshot.sampled_at >= start)
                .order_by(ExchangeRateSnapshot.sampled_at)
            )
        ).all()
    return [(row.sampled_at, row.value) for row in rows]


def _monthly_points(now_kst: datetime, current: float) -> list[tuple[datetime, float]]:
    start = now_kst.date() - timedelta(days=31)
    raw = kis_client.get_overseas_period_price(
        _MARKET_DIV,
        _SYMBOL,
        start.strftime("%Y%m%d"),
        now_kst.strftime("%Y%m%d"),
        "D",
    )
    by_day: dict[date, float] = {}
    for row in raw.get("output2") or []:
        raw_day = str(row.get("stck_bsop_date") or "")
        value = _number(row, "ovrs_nmix_prpr", "stck_clpr")
        if len(raw_day) == 8 and raw_day.isdigit() and value is not None and value > 0:
            day = datetime.strptime(raw_day, "%Y%m%d").date()
            if day >= start:
                by_day[day] = value

    # 오늘 일봉이 아직 없거나 종가 상태여도 가장 최근 30분 현재가로 교체한다.
    by_day[now_kst.date()] = current
    points = [(datetime.combine(day, time.min), value) for day, value in sorted(by_day.items())]
    return _evenly_spaced(points)


async def refresh() -> None:
    """현재가를 저장하고 세 기간 캐시를 한 번에 갱신한다. 실패하면 기존 캐시를 유지한다."""
    now_kst = datetime.now(_KST)
    sampled_at = _floor_half_hour(now_kst).replace(tzinfo=None)
    raw_current = await asyncio.to_thread(kis_client.get_overseas_index_or_fx_price, _MARKET_DIV, _SYMBOL)
    output = raw_current.get("output1") or {}
    current = _number(output, "ovrs_nmix_prpr")
    if current is None or current <= 0:
        raise ValueError("KIS 원/달러 현재값이 비어 있습니다.")

    await _save_snapshot(sampled_at, current)
    today_start = datetime.combine(now_kst.date(), time.min)
    today_all = await _snapshot_points(today_start)
    five_day_start = sampled_at - timedelta(days=5)
    five_day_all = await _snapshot_points(five_day_start)
    today = today_all[-_POINT_COUNT:]
    five_day = _evenly_spaced(five_day_all)
    month = await asyncio.to_thread(_monthly_points, now_kst, current)
    updated_at = datetime.now(UTC)

    new_cache = {
        "today": _payload("today", today, updated_at),
        # 8건만 모였다는 이유로 5일 차트가 완성됐다고 표시하지 않는다.
        # 최초 관측값이 범위 시작의 첫 30분 안에 있어야 실제 5일을 확보한 것으로 본다.
        "5d": _payload(
            "5d",
            five_day,
            updated_at,
            is_complete=(
                len(five_day) == _POINT_COUNT
                and bool(five_day_all)
                and five_day_all[0][0] <= five_day_start + timedelta(minutes=30)
            ),
        ),
        "1m": _payload("1m", month, updated_at),
    }
    with _lock:
        _cache.clear()
        _cache.update(new_cache)
    logger.info("원/달러 환율 갱신 완료 - %.2f (오늘 %d, 5일 %d, 월간 %d개)", current, len(today), len(five_day), len(month))


def get_exchange_rate(period: str) -> ExchangeRateResponse | None:
    with _lock:
        cached = _cache.get(period)
        copied = dict(cached) if cached is not None else None
    return ExchangeRateResponse(**copied) if copied is not None else None
