# kis_client.py
# 한국투자증권(KIS) API 직접 호출
# 토큰 발급 및 캐싱
# 국내/해외 지수, 환율 조회
#
# core에 있는 이유: 여러 도메인(timeline, heatmap 등)이 같이 쓸 수 있어야 하기 때문. 특히 토큰
# 발급/캐싱은 계좌 단위라서, 도메인마다 따로 만들면 재발급이 겹치거나 중복돼서 여기 하나로 모아둔다.

from __future__ import annotations

import json
import time
from pathlib import Path

import httpx

from backend.core.config import get_settings

# backend/src/backend/core/kis_client.py -> backend/ (프로젝트 최상위 폴더)
_TOKEN_CACHE_PATH = Path(__file__).resolve().parents[3] / ".cache" / "kis_token.json"
_TOKEN_ENDPOINT = "/oauth2/tokenP"
_INDEX_PRICE_ENDPOINT = "/uapi/domestic-stock/v1/quotations/inquire-index-price"
_INDEX_PRICE_TR_ID = "FHPUP02100000"
_OVERSEAS_INDEX_PRICE_ENDPOINT = "/uapi/overseas-price/v1/quotations/inquire-time-indexchartprice"
_OVERSEAS_INDEX_PRICE_TR_ID = "FHKST03030200"


# 캐시된 토큰 조회 (없거나 만료됐으면 None)
def _read_cached_token() -> str | None:
    if not _TOKEN_CACHE_PATH.exists():
        return None

    cached = json.loads(_TOKEN_CACHE_PATH.read_text())
    if cached["expires_at"] <= time.time():
        return None

    return cached["access_token"]


# 새로 발급받은 토큰을 파일로 저장
def _write_cached_token(access_token: str, expires_in: int) -> None:
    _TOKEN_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _TOKEN_CACHE_PATH.write_text(
        json.dumps(
            {
                "access_token": access_token,
                "expires_at": time.time() + expires_in - 60,  # 만료 60초 전까지는 캐시 재사용
            }
        )
    )


# API 호출용 토큰 발급 (저장된 토큰 있으면 재사용, 없으면 새로 발급)
# 주의: 토큰을 너무 자주 새로 발급받으면 계좌 주인한테 알림이 가니, 이 함수 안 거치고 따로 발급하지 말 것
def get_access_token() -> str:
    cached_token = _read_cached_token()
    if cached_token:
        return cached_token

    settings = get_settings()
    response = httpx.post(
        f"{settings.kis_base_url}{_TOKEN_ENDPOINT}",
        json={
            "grant_type": "client_credentials",
            "appkey": settings.kis_app_key,
            "appsecret": settings.kis_app_secret,
        },
    )
    response.raise_for_status()
    body = response.json()

    _write_cached_token(body["access_token"], body["expires_in"])
    return body["access_token"]


# 국내 지수(코스피/코스닥) 현재가 조회
# index_code로 지수 변경 가능 - 코스피="0001", 코스닥="1001"
def get_domestic_index_price(market_div_code: str, index_code: str) -> dict:
    settings = get_settings()
    response = httpx.get(
        f"{settings.kis_base_url}{_INDEX_PRICE_ENDPOINT}",
        headers={
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {get_access_token()}",
            "appkey": settings.kis_app_key,
            "appsecret": settings.kis_app_secret,
            "tr_id": _INDEX_PRICE_TR_ID,
            "custtype": "P",
        },
        params={
            "FID_COND_MRKT_DIV_CODE": market_div_code,
            "FID_INPUT_ISCD": index_code,
        },
    )
    response.raise_for_status()
    return response.json()


# 해외 지수/환율 현재가 조회
# symbol로 대상 변경 가능 - S&P500="SPX", 나스닥="COMP", 니케이="JP#NI225", 달러환율="FX@KRW"
# market_div_code는 지수면 "N", 환율이면 "X"
def get_overseas_index_or_fx_price(market_div_code: str, symbol: str) -> dict:
    settings = get_settings()
    response = httpx.get(
        f"{settings.kis_base_url}{_OVERSEAS_INDEX_PRICE_ENDPOINT}",
        headers={
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {get_access_token()}",
            "appkey": settings.kis_app_key,
            "appsecret": settings.kis_app_secret,
            "tr_id": _OVERSEAS_INDEX_PRICE_TR_ID,
            "custtype": "P",
        },
        params={
            "FID_COND_MRKT_DIV_CODE": market_div_code,
            "FID_INPUT_ISCD": symbol,
            "FID_HOUR_CLS_CODE": "0",
            "FID_PW_DATA_INCU_YN": "N",
        },
    )
    response.raise_for_status()
    return response.json()
