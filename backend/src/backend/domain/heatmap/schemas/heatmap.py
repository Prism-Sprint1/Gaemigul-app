"""히트맵 화면에 필요한 응답 형식. 거래량의 단위는 주, 시가총액은 원이다."""

from typing import Literal

from pydantic import BaseModel, Field

Market = Literal["kospi", "kosdaq"]
Period = Literal["day", "week", "month"]
MarketStatus = Literal["pre_open", "open", "closed", "holiday", "unknown"]


class HeatmapStock(BaseModel):
    code: str
    name: str
    price: float
    market_cap: float
    change_rate: float | None
    volume: int


class HeatmapSector(BaseModel):
    code: str
    name: str
    market_cap: float
    volume: int
    change_rate: float | None
    stocks: list[HeatmapStock]


class TopSector(BaseModel):
    code: str
    name: str
    volume: int
    volume_share: float
    change_rate: float | None


class Coverage(BaseModel):
    total_stocks: int = 0
    priced_stocks: int = 0
    missing_stocks: int = 0


class HeatmapResponse(BaseModel):
    market: Market
    period: Period
    updated_at: str | None = None
    as_of_date: str | None = None
    next_update_at: str | None = None
    market_status: MarketStatus = "unknown"
    is_stale: bool = True
    is_refreshing: bool = False
    message: str | None = None
    coverage: Coverage = Field(default_factory=Coverage)
    top_sector: TopSector | None = None
    sectors: list[HeatmapSector] = Field(default_factory=list)
