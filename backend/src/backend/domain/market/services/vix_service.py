# vix_service.py
# 메인 페이지 VIX 공포지수를 30분 캐시에 보관한다.
# 스케줄러만 KIS를 호출하고 GET /market/vix는 마지막 정상 캐시만 읽는다.

import logging
from datetime import UTC, date, datetime, timedelta
from threading import Lock

from backend.core import kis_client
from backend.domain.market.schemas.vix import VixResponse

logger = logging.getLogger(__name__)

_VIX_MARKET_DIV = "N"
_VIX_SYMBOL = "VIX"
_cache: dict | None = None
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


def _date(row: dict, *keys: str) -> date | None:
    for key in keys:
        raw = str(row.get(key) or "")
        if len(raw) == 8 and raw.isdigit():
            return datetime.strptime(raw, "%Y%m%d").date()
    return None


def _previous_close(current: float, market_date: date | None) -> float:
    """현재가 응답에 포인트 차이가 없을 때 최근 일봉에서 전일 종가를 찾는다."""
    end = market_date or datetime.now(UTC).date()
    start = end - timedelta(days=14)
    rows = kis_client.get_overseas_period_price(
        _VIX_MARKET_DIV,
        _VIX_SYMBOL,
        start.strftime("%Y%m%d"),
        end.strftime("%Y%m%d"),
        "D",
    ).get("output2") or []
    parsed = [
        (_date(row, "stck_bsop_date"), _number(row, "ovrs_nmix_prpr", "stck_clpr"))
        for row in rows
    ]
    parsed = [(day, price) for day, price in parsed if day is not None and price is not None and price > 0]
    parsed.sort(key=lambda item: item[0], reverse=True)
    if market_date is not None:
        previous = next((price for day, price in parsed if day < market_date), None)
    else:
        previous = parsed[1][1] if len(parsed) > 1 and abs(parsed[0][1] - current) < 0.005 else (parsed[0][1] if parsed else None)
    if previous is None:
        raise ValueError("VIX 전일 종가를 찾지 못했습니다.")
    return previous


def _parse(raw: dict) -> dict:
    output = raw.get("output1") or {}
    value = _number(output, "ovrs_nmix_prpr")
    if value is None or value <= 0:
        raise ValueError("KIS VIX 현재값이 비어 있습니다.")

    market_date = _date(output, "stck_bsop_date", "bass_dt", "xymd")
    change = _number(output, "prdy_vrss", "ovrs_nmix_prdy_vrss")
    change_rate = _number(output, "prdy_ctrt")
    # 일부 KIS 응답은 전일 대비 값과 부호 코드를 따로 줄 수 있어 등락률 방향으로 부호를 맞춘다.
    if change is not None and change_rate is not None:
        change = -abs(change) if change_rate < 0 else (abs(change) if change_rate > 0 else 0.0)
    if change is None:
        change = value - _previous_close(value, market_date)

    return {
        "value": round(value, 2),
        "change_value": round(change, 2),
        "market_date": market_date,
        "updated_at": datetime.now(UTC),
    }


def refresh() -> None:
    """KIS에서 새 값을 받아 캐시한다. 실패하면 예외를 올리고 기존 정상 캐시는 유지한다."""
    global _cache
    parsed = _parse(kis_client.get_overseas_index_or_fx_price(_VIX_MARKET_DIV, _VIX_SYMBOL))
    with _lock:
        _cache = parsed
    logger.info("VIX 갱신 완료 - %.2f (%+.2f)", parsed["value"], parsed["change_value"])


def get_vix() -> VixResponse | None:
    with _lock:
        cached = dict(_cache) if _cache is not None else None
    return VixResponse(**cached) if cached is not None else None
