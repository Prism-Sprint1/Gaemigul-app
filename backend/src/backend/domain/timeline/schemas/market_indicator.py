"""GET /timeline/indicators가 돌려주는 데이터 형태(응답 모양)를 정의하는 파일."""

from datetime import datetime

from pydantic import BaseModel


class MarketIndicatorItem(BaseModel):
    """지표 카드 하나에 들어가는 값."""

    code: str  # 내부에서 구분용으로 쓰는 값 (kospi, kosdaq 등)
    name: str  # 화면에 보여줄 이름 (KOSPI, KOSDAQ 등)
    price: float  # 현재가
    change_rate: float  # 전일 대비 등락률(%). 0보다 크면 상승, 작으면 하락


class IndicatorBarResponse(BaseModel):
    """GET /timeline/indicators가 최종적으로 돌려주는 전체 응답."""

    updated_at: datetime  # 이 응답을 만든 시각
    items: list[MarketIndicatorItem]
