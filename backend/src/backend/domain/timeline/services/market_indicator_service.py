# market_indicator_service.py
# 최상단 지표 바(코스피·코스닥·나스닥·S&P500·환율·니케이)의 값을 캐시에 담고 응답으로 만든다.
# 스케줄러가 refresh_all()로 캐시를 채우고, 라우터는 get_indicators()로 캐시를 읽기만 한다.

from datetime import UTC, datetime

from backend.core import kis_client
from backend.domain.timeline.schemas.market_indicator import (
    IndicatorBarResponse,
    MarketIndicatorItem,
)
from backend.domain.timeline.services import market_hours

# 화면에 보여줄 지표. (내부코드, 화면 이름, kind, market_div_code, 심볼) - 적힌 순서대로 화면에 나간다
#   - 지표를 추가하려면 한 줄 추가한다 (내부코드는 market_hours._MARKET_HOURS에도 넣을 것)
#   - 심볼을 바꾸면 다른 지수를 가져온다 (예: "COMP" -> "NDX"면 나스닥100)
#   - kind: "domestic"(국내지수) / "overseas"(해외지수·환율). 어느 KIS 함수를 부를지 정한다
_INDICATOR_DEFS = [
    ("kospi", "KOSPI", "domestic", "U", "0001"),
    ("kosdaq", "KOSDAQ", "domestic", "U", "1001"),
    ("nasdaq", "NASDAQ", "overseas", "N", "COMP"),
    ("sp500", "S&P500", "overseas", "N", "SPX"),
    ("usdkrw", "USD/KRW", "overseas", "X", "FX@KRW"),
    ("nikkei", "NIKKEI", "overseas", "N", "JP#NI225"),
]

# 지표별 마지막 값. code -> {code, name, price, change_rate, updated_at}
_cache: dict[str, dict] = {}


# 지표 하나를 KIS에서 받아 캐시에 넣는다
def _refresh_one(code: str, name: str, kind: str, market_div: str, symbol: str) -> None:
    if kind == "domestic":
        raw = kis_client.get_domestic_index_price(market_div, symbol)
        price = float(raw["output"]["bstp_nmix_prpr"])
        change_rate = float(raw["output"]["bstp_nmix_prdy_ctrt"])
    else:
        raw = kis_client.get_overseas_index_or_fx_price(market_div, symbol)
        price = float(raw["output1"]["ovrs_nmix_prpr"])
        change_rate = float(raw["output1"]["prdy_ctrt"])

    _cache[code] = {
        "code": code,
        "name": name,
        "price": price,
        "change_rate": change_rate,
        "updated_at": datetime.now(UTC).isoformat(),
    }


# 캐시 전체 갱신. 장이 닫힌 지표는 건너뛰고 이전 값을 유지한다(환율은 항상 갱신)
# 호출 주기는 main.py의 스케줄러에서 정한다
# force=True: 장 상태와 상관없이 전부 갱신 (서버 기동 시, 슬롯이 최신 값을 받아야 할 때)
# now: 특정 시각 기준으로 판단할 때만 넣는다
def refresh_all(now: datetime | None = None, *, force: bool = False) -> None:
    for code, name, kind, market_div, symbol in _INDICATOR_DEFS:
        if not force and code not in market_hours.ALWAYS_REFRESH_CODES and not market_hours.is_market_open(code, now):
            continue
        _refresh_one(code, name, kind, market_div, symbol)


# 캐시 복사본. 타임라인 슬롯이 지표 값을 읽을 때 쓴다
def get_cache_snapshot() -> dict[str, dict]:
    return dict(_cache)


# GET /timeline/indicators 응답. 캐시만 읽고 KIS는 부르지 않는다
def get_indicators() -> IndicatorBarResponse:
    items = [
        MarketIndicatorItem(
            code=cached["code"],
            name=cached["name"],
            price=cached["price"],
            change_rate=cached["change_rate"],
        )
        for code, _, _, _, _ in _INDICATOR_DEFS
        if (cached := _cache.get(code)) is not None
    ]
    return IndicatorBarResponse(updated_at=datetime.now(UTC), items=items)
