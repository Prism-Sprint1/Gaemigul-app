# 메인 페이지 투자자별 수급 응답. 금액 단위는 KIS 원본과 같은 백만원이다.

from datetime import date, datetime

from pydantic import BaseModel


class InvestorFlowResponse(BaseModel):
    individual: int
    institution: int
    foreign: int
    unit: str = "million_krw"
    market_date: date
    updated_at: datetime
