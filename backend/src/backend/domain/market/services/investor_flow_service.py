# 코스피·코스닥 투자자별 순매수 금액을 합산해 30분 메모리 캐시에 보관한다.
# 음수는 순매도, 양수는 순매수이며 단위는 백만원이다.

import logging
from datetime import UTC, date, datetime
from threading import Lock
from zoneinfo import ZoneInfo

from backend.core import kis_client
from backend.domain.market.schemas.investor_flow import InvestorFlowResponse

logger = logging.getLogger(__name__)

_KST = ZoneInfo("Asia/Seoul")
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


def _day(row: dict) -> date | None:
    raw = str(row.get("stck_bsop_date") or "")
    return datetime.strptime(raw, "%Y%m%d").date() if len(raw) == 8 and raw.isdigit() else None


def fetch_raw(today: date) -> dict:
    """두 시장 원본을 한 번씩 조회한다. 시장심리지수도 이 반환값을 재사용한다."""
    ymd = today.strftime("%Y%m%d")
    return {
        "foreign_kospi": kis_client.get_investor_daily_by_market(ymd, "KSP", "0001"),
        "foreign_kosdaq": kis_client.get_investor_daily_by_market(ymd, "KSQ", "1001"),
    }


def _parse(raw: dict) -> dict:
    rows_by_market: list[dict[date, dict]] = []
    for key in ("foreign_kospi", "foreign_kosdaq"):
        dated = {day: row for row in raw[key].get("output") or [] if (day := _day(row)) is not None}
        if not dated:
            raise ValueError(f"KIS {key} 투자자 수급이 비어 있습니다.")
        rows_by_market.append(dated)

    common_days = set(rows_by_market[0]) & set(rows_by_market[1])
    if not common_days:
        raise ValueError("코스피·코스닥의 공통 수급 거래일이 없습니다.")
    market_date = max(common_days)
    keys = {
        "individual": "prsn_ntby_tr_pbmn",
        "institution": "orgn_ntby_tr_pbmn",
        "foreign": "frgn_ntby_tr_pbmn",
    }
    values: dict[str, int] = {}
    for name, source_key in keys.items():
        amounts = [_number(rows[market_date], source_key) for rows in rows_by_market]
        if any(amount is None for amount in amounts):
            raise ValueError(f"{market_date} {name} 순매수 금액이 비어 있습니다.")
        values[name] = sum(amount for amount in amounts if amount is not None)

    return {
        **values,
        "unit": "million_krw",
        "market_date": market_date,
        "updated_at": datetime.now(UTC),
    }


def refresh(raw: dict | None = None) -> dict:
    """수급 캐시를 갱신하고 시장심리지수가 재사용할 KIS 원본을 돌려준다."""
    global _cache
    source = raw or fetch_raw(datetime.now(_KST).date())
    parsed = _parse(source)
    with _lock:
        _cache = parsed
    logger.info(
        "투자자 수급 갱신 완료 - 개인 %+,d / 기관 %+,d / 외국인 %+,d백만원 (%s)",
        parsed["individual"],
        parsed["institution"],
        parsed["foreign"],
        parsed["market_date"],
    )
    return source


def get_investor_flow() -> InvestorFlowResponse | None:
    with _lock:
        cached = dict(_cache) if _cache is not None else None
    return InvestorFlowResponse(**cached) if cached is not None else None
