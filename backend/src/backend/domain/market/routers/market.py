# market.py
# 메인 페이지가 쓰는 시장 공통 데이터 API.

from fastapi import APIRouter, HTTPException

from backend.domain.market.schemas.exchange_rate import ExchangeRatePeriod, ExchangeRateResponse
from backend.domain.market.schemas.investor_flow import InvestorFlowResponse
from backend.domain.market.schemas.sentiment import SentimentResponse
from backend.domain.market.schemas.trading_value import TradingValueDistributionResponse
from backend.domain.market.schemas.vix import VixResponse
from backend.domain.market.services import exchange_rate_service, investor_flow_service, sentiment_service, trading_value_service, vix_service

router = APIRouter(prefix="/market", tags=["market"])


# 소비자 공포 지수
@router.get("/vix", response_model=VixResponse)
def get_vix() -> VixResponse:
    cached = vix_service.get_vix()
    if cached is None:
        raise HTTPException(status_code=503, detail="VIX 데이터가 아직 준비되지 않았습니다.")
    return cached


# 소비자 심리 지수(개미굴 전용)
@router.get("/sentiment", response_model=SentimentResponse)
def get_sentiment() -> SentimentResponse:
    cached = sentiment_service.get_sentiment()
    if cached is None:
        raise HTTPException(status_code=503, detail="개미굴 시장심리지수가 아직 준비되지 않았습니다.")
    return cached


# 원/달러 환율 차트 (오늘·5일·1개월)
@router.get("/exchange-rate", response_model=ExchangeRateResponse)
def get_exchange_rate(period: ExchangeRatePeriod = "today") -> ExchangeRateResponse:
    cached = exchange_rate_service.get_exchange_rate(period)
    if cached is None:
        raise HTTPException(status_code=503, detail="원/달러 환율 데이터가 아직 준비되지 않았습니다.")
    return cached


# 개인·기관·외국인 순매수 금액 (코스피+코스닥, 음수=순매도, 양수=순매수)
@router.get("/investor-flow", response_model=InvestorFlowResponse)
def get_investor_flow() -> InvestorFlowResponse:
    cached = investor_flow_service.get_investor_flow()
    if cached is None:
        raise HTTPException(status_code=503, detail="투자자 수급 데이터가 아직 준비되지 않았습니다.")
    return cached


# 정규장 30분 구간별 거래대금 (15:30 완성 전에는 최근 완성 거래일)
@router.get("/trading-value-distribution", response_model=TradingValueDistributionResponse)
def get_trading_value_distribution() -> TradingValueDistributionResponse:
    cached = trading_value_service.get_trading_value_distribution()
    if cached is None:
        raise HTTPException(status_code=503, detail="시간대별 거래대금 데이터가 아직 준비되지 않았습니다.")
    return cached
