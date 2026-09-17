# 메인 페이지 개미굴 시장심리지수 응답. 라벨은 프런트에서 점수 구간에 맞춰 표시한다.

from datetime import date, datetime

from pydantic import BaseModel, Field


class SentimentResponse(BaseModel):
    score: float = Field(ge=0, le=100)
    market_date: date
    updated_at: datetime
