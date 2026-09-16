# market.py
# 메인 페이지가 쓰는 시장 공통 데이터 API.

from fastapi import APIRouter, HTTPException

from backend.domain.market.schemas.vix import VixResponse
from backend.domain.market.services import vix_service

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/vix", response_model=VixResponse)
def get_vix() -> VixResponse:
    cached = vix_service.get_vix()
    if cached is None:
        raise HTTPException(status_code=503, detail="VIX 데이터가 아직 준비되지 않았습니다.")
    return cached
