# 메인 페이지 개미굴 시장심리지수를 계산해 30분 메모리 캐시에 보관한다.
# 최근 60거래일 기준 분포는 하루 한 번만 갱신하며 GET API는 KIS를 호출하지 않는다.

import logging
from datetime import UTC, date, datetime, timedelta
from threading import Lock
from zoneinfo import ZoneInfo

from backend.core import kis_client
from backend.domain.market.schemas.sentiment import SentimentResponse

logger = logging.getLogger(__name__)

_KOSPI = "0001"
_KOSDAQ = "1001"
_VKOSPI = "0503"
_FX_MARKET = "X"
_FX_SYMBOL = "FX@KRW"
_REFERENCE_DAYS = 60
_MIN_REFERENCE_DAYS = 20
_KST = ZoneInfo("Asia/Seoul")

_WEIGHTS = {
    "momentum": 0.30,
    "breadth": 0.25,
    "foreign_flow": 0.20,
    "volatility": 0.15,
    "fx": 0.10,
}

_cache: dict | None = None
_reference_cache: dict | None = None
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


def _day(row: dict) -> date | None:
    raw = str(row.get("stck_bsop_date") or row.get("bass_dt") or row.get("xymd") or "")
    return datetime.strptime(raw, "%Y%m%d").date() if len(raw) == 8 and raw.isdigit() else None


def _dated_rows(raw: dict) -> dict[date, dict]:
    return {day: row for row in (raw.get("output2") or []) if (day := _day(row)) is not None}


def _latest_market_date(raw: dict) -> date:
    rows = _dated_rows(raw)
    if not rows:
        raise ValueError("KIS 국내 지수 거래일이 비어 있습니다.")
    return max(rows)


def _percentile(value: float, references: list[float]) -> float:
    values = sorted(item for item in references if item is not None)
    if len(values) < _MIN_REFERENCE_DAYS:
        raise ValueError(f"시장심리지수 기준 데이터가 부족합니다 ({len(values)}일).")
    below = sum(item < value for item in values)
    equal = sum(item == value for item in values)
    return 100 * (below + equal * 0.5) / len(values)


def _index_history(kospi: dict, kosdaq: dict) -> tuple[list[float], dict[date, float]]:
    kospi_rows, kosdaq_rows = _dated_rows(kospi), _dated_rows(kosdaq)
    common = sorted(set(kospi_rows) & set(kosdaq_rows), reverse=True)
    momentum, turnover = [], {}
    for day in common:
        kospi_change = _number(kospi_rows[day], "bstp_nmix_prdy_ctrt")
        kosdaq_change = _number(kosdaq_rows[day], "bstp_nmix_prdy_ctrt")
        kospi_turnover = _number(kospi_rows[day], "acml_tr_pbmn")
        kosdaq_turnover = _number(kosdaq_rows[day], "acml_tr_pbmn")
        if kospi_change is not None and kosdaq_change is not None:
            momentum.append(kospi_change * 0.7 + kosdaq_change * 0.3)
        if kospi_turnover is not None and kosdaq_turnover is not None and kospi_turnover + kosdaq_turnover > 0:
            turnover[day] = kospi_turnover + kosdaq_turnover
    return momentum[:_REFERENCE_DAYS], turnover


def _foreign_history(kospi: dict, kosdaq: dict, turnover: dict[date, float]) -> list[float]:
    kospi_rows = {day: row for row in (kospi.get("output") or []) if (day := _day(row)) is not None}
    kosdaq_rows = {day: row for row in (kosdaq.get("output") or []) if (day := _day(row)) is not None}
    values = []
    for day in sorted(set(kospi_rows) & set(kosdaq_rows) & set(turnover), reverse=True):
        first = _number(kospi_rows[day], "frgn_ntby_tr_pbmn")
        second = _number(kosdaq_rows[day], "frgn_ntby_tr_pbmn")
        if first is not None and second is not None:
            values.append((first + second) / turnover[day])
    return values[:_REFERENCE_DAYS]


def _level_history(raw: dict, *keys: str) -> list[float]:
    rows = sorted(_dated_rows(raw).items(), reverse=True)
    return [value for _, row in rows if (value := _number(row, *keys)) is not None and value > 0][:_REFERENCE_DAYS]


def _change_history(raw: dict, *keys: str) -> list[float]:
    rows = sorted(_dated_rows(raw).items())
    prices = [(day, value) for day, row in rows if (value := _number(row, *keys)) is not None and value > 0]
    changes = [100 * (current / previous - 1) for (_, previous), (_, current) in zip(prices, prices[1:]) if previous > 0]
    return list(reversed(changes))[:_REFERENCE_DAYS]


def _fetch_raw(today: date, investor_raw: dict | None = None) -> dict:
    start = today - timedelta(days=120)
    ymd = today.strftime("%Y%m%d")
    raw = {
        "kospi": kis_client.get_index_daily_price(_KOSPI, ymd, "D"),
        "kosdaq": kis_client.get_index_daily_price(_KOSDAQ, ymd, "D"),
        "vkospi": kis_client.get_index_daily_price(_VKOSPI, ymd, "D"),
        "fx_history": kis_client.get_overseas_period_price(_FX_MARKET, _FX_SYMBOL, start.strftime("%Y%m%d"), ymd, "D"),
        "fx_current": kis_client.get_overseas_index_or_fx_price(_FX_MARKET, _FX_SYMBOL),
    }
    raw.update(
        investor_raw
        or {
            "foreign_kospi": kis_client.get_investor_daily_by_market(ymd, "KSP", _KOSPI),
            "foreign_kosdaq": kis_client.get_investor_daily_by_market(ymd, "KSQ", _KOSDAQ),
        }
    )
    return raw


def _build_references(raw: dict, today: date) -> dict:
    momentum, turnover = _index_history(raw["kospi"], raw["kosdaq"])
    references = {
        "cached_on": today,
        "momentum": momentum,
        "foreign_flow": _foreign_history(raw["foreign_kospi"], raw["foreign_kosdaq"], turnover),
        "volatility": _level_history(raw["vkospi"], "bstp_nmix_prpr"),
        "fx": _change_history(raw["fx_history"], "ovrs_nmix_prpr", "stck_clpr"),
    }
    for name in ("momentum", "foreign_flow", "volatility", "fx"):
        if len(references[name]) < _MIN_REFERENCE_DAYS:
            raise ValueError(f"시장심리지수 {name} 기준 데이터가 부족합니다 ({len(references[name])}일).")
    return references


def _current_index(raw: dict) -> tuple[float, float, float]:
    kospi, kosdaq = raw["kospi"].get("output1") or {}, raw["kosdaq"].get("output1") or {}
    kospi_change = _number(kospi, "bstp_nmix_prdy_ctrt")
    kosdaq_change = _number(kosdaq, "bstp_nmix_prdy_ctrt")
    if kospi_change is None or kosdaq_change is None:
        raise ValueError("코스피·코스닥 현재 등락률이 비어 있습니다.")

    rising = (_number(kospi, "ascn_issu_cnt") or 0) + (_number(kosdaq, "ascn_issu_cnt") or 0)
    falling = (_number(kospi, "down_issu_cnt") or 0) + (_number(kosdaq, "down_issu_cnt") or 0)
    flat = (_number(kospi, "stnr_issu_cnt") or 0) + (_number(kosdaq, "stnr_issu_cnt") or 0)
    if rising + falling + flat <= 0:
        raise ValueError("코스피·코스닥 상승·하락 종목 수가 비어 있습니다.")
    return kospi_change * 0.7 + kosdaq_change * 0.3, 100 * rising / (rising + falling + flat), (_number(kospi, "acml_tr_pbmn") or 0) + (_number(kosdaq, "acml_tr_pbmn") or 0)


def _current_foreign(raw: dict, market_date: date, turnover: float) -> float:
    if turnover <= 0:
        raise ValueError("현재 시장 거래대금이 비어 있습니다.")
    total = 0.0
    for key in ("foreign_kospi", "foreign_kosdaq"):
        rows = _dated_rows({"output2": raw[key].get("output") or []})
        row = rows.get(market_date)
        value = _number(row or {}, "frgn_ntby_tr_pbmn")
        if value is None:
            raise ValueError(f"{market_date} 외국인 순매수 값이 비어 있습니다.")
        total += value
    return total / turnover


def _current_fx_change(raw: dict) -> float:
    current = raw["fx_current"].get("output1") or {}
    change = _number(current, "prdy_ctrt")
    if change is not None:
        return change
    history = _change_history(raw["fx_history"], "ovrs_nmix_prpr", "stck_clpr")
    if not history:
        raise ValueError("원·달러 환율 등락률이 비어 있습니다.")
    return history[0]


def _calculate(raw: dict, references: dict) -> dict:
    market_date = _latest_market_date(raw["kospi"])
    momentum, breadth, turnover = _current_index(raw)
    foreign_flow = _current_foreign(raw, market_date, turnover)
    volatility = _number(raw["vkospi"].get("output1") or {}, "bstp_nmix_prpr")
    if volatility is None or volatility <= 0:
        raise ValueError("VKOSPI 현재값이 비어 있습니다.")
    fx_change = _current_fx_change(raw)

    components = {
        "momentum": _percentile(momentum, references["momentum"]),
        "breadth": breadth,
        "foreign_flow": _percentile(foreign_flow, references["foreign_flow"]),
        "volatility": 100 - _percentile(volatility, references["volatility"]),
        "fx": 100 - _percentile(fx_change, references["fx"]),
    }
    score = sum(components[name] * weight for name, weight in _WEIGHTS.items())
    return {"score": round(max(0, min(100, score)), 1), "market_date": market_date, "updated_at": datetime.now(UTC)}


def refresh(investor_raw: dict | None = None) -> None:
    """KIS 현재값으로 점수를 계산한다. 실패하면 예외를 올리고 기존 정상 캐시는 유지한다."""
    global _cache, _reference_cache
    today = datetime.now(_KST).date()
    raw = _fetch_raw(today, investor_raw)
    with _lock:
        references = _reference_cache
    if references is None or references["cached_on"] != today:
        references = _build_references(raw, today)

    parsed = _calculate(raw, references)
    with _lock:
        _reference_cache = references
        _cache = parsed
    logger.info("개미굴 시장심리지수 갱신 완료 - %.1f점 (%s)", parsed["score"], parsed["market_date"])


def get_sentiment() -> SentimentResponse | None:
    with _lock:
        cached = dict(_cache) if _cache is not None else None
    return SentimentResponse(**cached) if cached is not None else None
