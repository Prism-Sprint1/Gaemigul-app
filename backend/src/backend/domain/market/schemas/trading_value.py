# 메인 페이지 시간대별 거래대금 분포 응답. 금액 단위는 백만원이다.

from datetime import date, datetime

from pydantic import BaseModel, Field


class TradingValuePoint(BaseModel):
    time_slot: str
    amount: int = Field(ge=0)


class TradingValueDistributionResponse(BaseModel):
    market_date: date
    points: list[TradingValuePoint]
    unit: str = "million_krw"
    updated_at: datetime
