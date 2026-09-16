# vix.py
# 메인 페이지 VIX 공포지수 응답. value는 현재(또는 마지막) 수치, change_value는 전일 종가 대비 포인트 차이다.

from datetime import date, datetime

from pydantic import BaseModel


class VixResponse(BaseModel):
    value: float
    change_value: float
    market_date: date | None
    updated_at: datetime
