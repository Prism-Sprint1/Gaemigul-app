# 메인 페이지 원/달러 환율 차트 응답.

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ExchangeRatePeriod = Literal["today", "5d", "1m"]


class ExchangeRatePoint(BaseModel):
    timestamp: datetime
    value: float = Field(gt=0)


class ExchangeRateResponse(BaseModel):
    period: ExchangeRatePeriod
    points: list[ExchangeRatePoint]
    requested_point_count: int = 8
    is_complete: bool
    updated_at: datetime
