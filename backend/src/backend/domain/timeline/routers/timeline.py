# timeline.py
# 엔드 포인트 및 URL 주소 매핑

from fastapi import APIRouter

from backend.domain.timeline.schemas.market_indicator import IndicatorBarResponse
from backend.domain.timeline.services import market_indicator_service

router = APIRouter(prefix="/timeline", tags=["timeline"])


# 최상단 지표 바 데이터 조회
# 캐시에서 바로 읽기 때문에 이 요청 자체는 KIS를 호출하지 않는다
@router.get("/indicators", response_model=IndicatorBarResponse)
def get_indicators() -> IndicatorBarResponse:
    return market_indicator_service.get_indicators()
