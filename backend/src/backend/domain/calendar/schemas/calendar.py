from pydantic import BaseModel
from typing import Optional


class CalendarEvent(BaseModel):
    # 날짜
    date: str
    # 시간
    time: Optional[str] = None
    # 국가
    country: str
    # 카테고리
    category: str
    # 이벤트명
    title: str
    # 중요도
    importance: int
    # 이전 값
    previous: Optional[str] = None
    # 예측 값
    forecast: Optional[str] = None
    # 실제 값
    actual: Optional[str] = None
    # 발표상태
    status: str