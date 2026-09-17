"""읽기 전용 히트맵 API. 화면 조회와 UPDATE 버튼은 KIS를 직접 호출하지 않는다."""

from fastapi import APIRouter

from backend.domain.heatmap.schemas.heatmap import HeatmapResponse, Market, Period
from backend.domain.heatmap.services import heatmap

router = APIRouter(prefix="/heatmap", tags=["heatmap"])


@router.get("", response_model=HeatmapResponse)
def get_heatmap(market: Market = "kospi", period: Period = "day") -> HeatmapResponse:
    return heatmap.get_heatmap(market, period)
