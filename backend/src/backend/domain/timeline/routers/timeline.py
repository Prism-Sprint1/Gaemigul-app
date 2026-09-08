"""timeline 도메인의 API 주소(라우터)를 모아둔 파일."""

from fastapi import APIRouter

from backend.domain.timeline.schemas.market_indicator import IndicatorBarResponse
from backend.domain.timeline.services import market_indicator_service

router = APIRouter(prefix="/timeline", tags=["timeline"])


@router.get("/indicators", response_model=IndicatorBarResponse)
def get_indicators() -> IndicatorBarResponse:
    """최상단 지표 바 데이터를 반환한다. 캐시에서 바로 읽기 때문에 이 요청 자체는 KIS를 호출하지 않는다."""
    return market_indicator_service.get_indicators()
