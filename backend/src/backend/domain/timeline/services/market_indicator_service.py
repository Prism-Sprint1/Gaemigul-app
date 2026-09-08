"""KIS에서 받아온 데이터를 가공해서 저장해두는 파일.

스케줄러(main.py)가 주기적으로 refresh_all()을 실행해서 캐시를 채우고, 라우터는 get_indicators()로
그 캐시를 읽기만 한다 — 이래야 "장마감이면 값 고정"이 의미가 있다.
"""

from datetime import UTC, datetime

from backend.domain.timeline.schemas.market_indicator import (
    IndicatorBarResponse,
    MarketIndicatorItem,
)
from backend.domain.timeline.services import kis_client, market_hours

# 화면에 보여줄 지표 목록. (내부코드, 화면에 보일 이름, kind, market_div_code, 종목/심볼코드) 순서.
# 이 리스트에 적힌 순서 그대로 화면에 나간다.
#
# 이 리스트 값을 바꾸면 이렇게 바뀐다:
#   - kospi 줄의 마지막 값("0001")을 다른 코드로 바꾸면 코스피 대신 다른 국내지수를 가져온다.
#   - nasdaq 줄의 "COMP"를 "NDX"로 바꾸면 나스닥종합 대신 나스닥100을 가져온다.
#   - 지표를 새로 추가하고 싶으면 이 리스트에 한 줄만 추가하면 된다.
#   - kind는 "domestic"(국내) 아니면 "overseas"(해외/환율) 둘 중 하나여야 한다 — 아래에서 이 값으로
#     어떤 kis_client 함수를 쓸지 정하기 때문.
_INDICATOR_DEFS = [
    ("kospi", "KOSPI", "domestic", "U", "0001"),
    ("kosdaq", "KOSDAQ", "domestic", "U", "1001"),
    ("nasdaq", "NASDAQ", "overseas", "N", "COMP"),
    ("sp500", "S&P500", "overseas", "N", "SPX"),
    ("usdkrw", "USD/KRW", "overseas", "X", "FX@KRW"),
    ("nikkei", "NIKKEI", "overseas", "N", "JP#NI225"),
]

# 지표별로 마지막에 가져온 값을 저장해두는 곳. code -> {code, name, price, change_rate, updated_at}
_cache: dict[str, dict] = {}


def _refresh_one(code: str, name: str, kind: str, market_div: str, symbol: str) -> None:
    """지표 하나를 KIS에서 가져와서 _cache[code]에 저장한다."""
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


def refresh_all(now: datetime | None = None, *, force: bool = False) -> None:
    """캐시를 전부 갱신한다. 스케줄러가 정시(00분/30분)마다 이 함수를 호출한다.

    장이 닫힌 지표는 건너뛰고 기존 캐시 값을 그대로 둔다(환율은 예외로 항상 갱신).
    force=True를 주면 장 상태 상관없이 전부 갱신한다 — 서버를 처음 켤 때 캐시를 채우는 용도로만 쓸 것.
    now는 테스트할 때 특정 시각을 넣어보기 위한 값 — 평소에는 안 넣어도 된다.
    """
    for code, name, kind, market_div, symbol in _INDICATOR_DEFS:
        if not force and code not in market_hours.ALWAYS_REFRESH_CODES and not market_hours.is_market_open(code, now):
            continue
        _refresh_one(code, name, kind, market_div, symbol)


def get_cache_snapshot() -> dict[str, dict]:
    """지금 캐시에 있는 값을 그대로 반환한다. 확인/테스트용."""
    return dict(_cache)


def get_indicators() -> IndicatorBarResponse:
    """라우터가 호출하는 함수. 캐시에 있는 값을 화면에 보낼 형태(IndicatorBarResponse)로 바꿔서 반환한다."""
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
