# 코스피·코스닥 30분 누적 거래대금을 구간 차액으로 바꿔 메모리 캐시에 보관한다.
# 오늘 15:30 값이 완성되기 전에는 가장 최근 완성 거래일의 14개 분포를 제공한다.

import logging
from datetime import UTC, date, datetime
from threading import Lock

from backend.core import kis_client
from backend.domain.market.schemas.trading_value import TradingValueDistributionResponse

logger = logging.getLogger(__name__)

_EXPECTED_TIMES = tuple(f"{hour:02d}{minute:02d}00" for hour in range(9, 16) for minute in (0, 30) if not (hour == 15 and minute > 30))
_cache: dict | None = None
_lock = Lock()


def _number(row: dict, key: str) -> int | None:
    raw = row.get(key)
    if raw in (None, ""):
        return None
    try:
        return int(float(str(raw).replace(",", "")))
    except ValueError:
        return None


def _rows_by_day(raw: dict) -> dict[date, dict[str, int]]:
    result: dict[date, dict[str, int]] = {}
    for row in raw.get("output2") or []:
        raw_day = str(row.get("stck_bsop_date") or "")
        raw_time = str(row.get("stck_cntg_hour") or "").zfill(6)
        amount = _number(row, "acml_tr_pbmn")
        if len(raw_day) != 8 or not raw_day.isdigit() or raw_time not in _EXPECTED_TIMES or amount is None or amount < 0:
            continue
        day = datetime.strptime(raw_day, "%Y%m%d").date()
        result.setdefault(day, {})[raw_time] = amount
    return result


def _parse(kospi_raw: dict, kosdaq_raw: dict) -> dict:
    kospi, kosdaq = _rows_by_day(kospi_raw), _rows_by_day(kosdaq_raw)
    complete_days = [
        day
        for day in set(kospi) & set(kosdaq)
        if all(slot in kospi[day] and slot in kosdaq[day] for slot in _EXPECTED_TIMES)
    ]
    if not complete_days:
        raise ValueError("KIS에서 완성된 시간대별 거래대금 거래일을 찾지 못했습니다.")
    market_date = max(complete_days)

    previous = 0
    points = []
    for slot in _EXPECTED_TIMES:
        cumulative = kospi[market_date][slot] + kosdaq[market_date][slot]
        amount = cumulative - previous
        if amount < 0:
            raise ValueError(f"{market_date} {slot} 누적 거래대금이 직전 값보다 작습니다.")
        points.append({"time_slot": f"{slot[:2]}:{slot[2:4]}", "amount": amount})
        previous = cumulative

    return {
        "market_date": market_date,
        "points": points,
        "unit": "million_krw",
        "updated_at": datetime.now(UTC),
    }


def refresh() -> None:
    """완성된 최신 거래일을 조회한다. 실패하면 예외를 올리고 기존 정상 캐시는 유지한다."""
    global _cache
    parsed = _parse(
        kis_client.get_index_minute_price("0001", "1800", True),
        kis_client.get_index_minute_price("1001", "1800", True),
    )
    with _lock:
        _cache = parsed
    logger.info("시간대별 거래대금 갱신 완료 - %s (%d개)", parsed["market_date"], len(parsed["points"]))


def get_trading_value_distribution() -> TradingValueDistributionResponse | None:
    with _lock:
        cached = dict(_cache) if _cache is not None else None
    return TradingValueDistributionResponse(**cached) if cached is not None else None
