"""한국투자증권(KIS) API를 직접 호출하는 파일. 토큰 발급이랑 국내/해외 지수·환율 조회 함수들이 있다."""

from __future__ import annotations

import json
import time
from pathlib import Path

import httpx

from backend.core.config import get_settings

# backend/src/backend/domain/timeline/services/kis_client.py -> backend/ (프로젝트 최상위 폴더)
_TOKEN_CACHE_PATH = Path(__file__).resolve().parents[5] / ".cache" / "kis_token.json"
_TOKEN_ENDPOINT = "/oauth2/tokenP"
_INDEX_PRICE_ENDPOINT = "/uapi/domestic-stock/v1/quotations/inquire-index-price"
_INDEX_PRICE_TR_ID = "FHPUP02100000"
_OVERSEAS_INDEX_PRICE_ENDPOINT = "/uapi/overseas-price/v1/quotations/inquire-time-indexchartprice"
_OVERSEAS_INDEX_PRICE_TR_ID = "FHKST03030200"


def _read_cached_token() -> str | None:
    """저장해둔 토큰이 있고 아직 안 만료됐으면 그 값을 돌려준다. 없거나 만료됐으면 None."""
    if not _TOKEN_CACHE_PATH.exists():
        return None

    cached = json.loads(_TOKEN_CACHE_PATH.read_text())
    if cached["expires_at"] <= time.time():
        return None

    return cached["access_token"]


def _write_cached_token(access_token: str, expires_in: int) -> None:
    """새로 발급받은 토큰을 파일로 저장해둔다."""
    _TOKEN_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _TOKEN_CACHE_PATH.write_text(
        json.dumps(
            {
                "access_token": access_token,
                # 만료 60초 전까지는 새로 발급받지 않고 이 캐시를 그대로 재사용한다.
                "expires_at": time.time() + expires_in - 60,
            }
        )
    )


def get_access_token() -> str:
    """API 호출용 토큰을 가져오는 함수. 저장된 토큰이 있으면 재사용하고, 없거나 만료됐으면 새로 발급받는다.

    토큰을 너무 자주 새로 발급받으면 계좌 주인한테 알림이 가니, 이 함수 안 거치고 따로 토큰 발급하지 말 것.
    """
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


def get_domestic_index_price(market_div_code: str, index_code: str) -> dict:
    """국내 지수(코스피/코스닥) 현재가를 가져온다.

    index_code를 바꾸면 다른 지수를 가져온다 — 코스피="0001", 코스닥="1001".
    """
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


def get_overseas_index_or_fx_price(market_div_code: str, symbol: str) -> dict:
    """해외 지수나 환율의 현재가를 가져온다.

    symbol을 바꾸면 다른 지수/환율을 가져온다 — S&P500="SPX", 나스닥="COMP", 니케이="JP#NI225", 달러환율="FX@KRW".
    market_div_code는 지수면 "N", 환율이면 "X".
    """
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
