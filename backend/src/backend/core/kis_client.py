# kis_client.py
# 한국투자증권(KIS) API 직접 호출
# 토큰 발급 및 캐싱
# 국내/해외 지수, 환율 조회
# 국내 업종 목록, 업종 내 종목 순위 조회
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
_INDEX_CATEGORY_ENDPOINT = "/uapi/domestic-stock/v1/quotations/inquire-index-category-price"
_INDEX_CATEGORY_TR_ID = "FHPUP02140000"
_FLUCTUATION_RANK_ENDPOINT = "/uapi/domestic-stock/v1/ranking/fluctuation"
_FLUCTUATION_RANK_TR_ID = "FHPST01700000"
_VOLUME_RANK_ENDPOINT = "/uapi/domestic-stock/v1/quotations/volume-rank"
_VOLUME_RANK_TR_ID = "FHPST01710000"
_INDEX_TICK_PRICE_ENDPOINT = "/uapi/domestic-stock/v1/quotations/inquire-index-timeprice"
_INDEX_TICK_PRICE_TR_ID = "FHPUP02110200"
_HOLIDAY_ENDPOINT = "/uapi/domestic-stock/v1/quotations/chk-holiday"
_HOLIDAY_TR_ID = "CTCA0903R"
_EXPECTED_RANK_ENDPOINT = "/uapi/domestic-stock/v1/ranking/exp-trans-updown"
_EXPECTED_RANK_TR_ID = "FHPST01820000"

# 조회 실패 시 재시도 설정 (토큰 발급에는 적용하지 않는다)
_RETRY_COUNT = 3
_RETRY_WAIT_SECONDS = 0.5
_TIMEOUT_SECONDS = 10.0


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


# 키가 설정돼 있는지 확인하고 설정값을 돌려준다
# 이 파일의 모든 공개 함수는 설정값을 여기서 받아야 한다 - get_access_token() 안에서만 검사하면
# 캐시된 토큰이 있을 때 검사를 건너뛰어서, 키가 없는데도 요청이 나가버린다
def _checked_settings():
    settings = get_settings()
    if not settings.kis_app_key or not settings.kis_app_secret:
        raise RuntimeError("KIS_APP_KEY / KIS_APP_SECRET가 .env에 없습니다. backend/.env에 추가해주세요.")
    return settings


# 조회 API가 공통으로 쓰는 요청 헤더를 만든다
# tr_id만 API마다 다르고 나머지는 전부 같아서 여기 한 곳에 모아뒀다 - 헤더 형식이 바뀌면 여기만 고치면 된다
def _headers(settings, tr_id: str) -> dict[str, str]:
    return {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {get_access_token()}",
        "appkey": settings.kis_app_key,
        "appsecret": settings.kis_app_secret,
        "tr_id": tr_id,
        "custtype": "P",
    }


# 조회 API 공통 GET. 일시적인 실패는 여기서 다시 시도한다
#
# 재시도하는 경우와 안 하는 경우를 나눈 이유:
#   - 5xx: 서버 쪽 일시 장애. KIS는 초당 호출 한도를 넘기면 HTTP 500 + msg_cd EGW00201을 준다(확인 완료).
#          주도 섹터는 한 번에 7회를 연달아 부르기 때문에 여기 걸릴 수 있어서 재시도가 반드시 필요하다
#   - 연결 오류(타임아웃 등): 네트워크 문제라 다시 보내면 될 수 있다
#   - 4xx: 요청 자체가 잘못된 것(파라미터 오류 등)이라 다시 보내도 결과가 같으므로 바로 에러를 낸다
#
# 재시도 횟수/대기 시간을 바꾸려면 아래 _RETRY_COUNT, _RETRY_WAIT_SECONDS를 고치면 된다
# 주의: 토큰 발급(get_access_token)에는 절대 쓰지 말 것 - 계좌 주인에게 알림이 여러 번 간다
def _get_with_retry(url: str, *, headers: dict, params: dict) -> dict:
    last_error = None

    for attempt in range(_RETRY_COUNT):
        try:
            response = httpx.get(url, headers=headers, params=params, timeout=_TIMEOUT_SECONDS)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as error:
            if error.response.status_code < 500:
                raise
            last_error = error
        except httpx.TransportError as error:
            last_error = error

        # 마지막 시도였으면 더 기다리지 않고 아래에서 에러를 낸다
        if attempt < _RETRY_COUNT - 1:
            time.sleep(_RETRY_WAIT_SECONDS * (attempt + 1))  # 시도할수록 조금씩 더 기다린다

    raise last_error



# API 호출용 토큰 발급 (저장된 토큰 있으면 재사용, 없으면 새로 발급)
# 주의: 토큰을 너무 자주 새로 발급받으면 계좌 주인한테 알림이 가니, 이 함수 안 거치고 따로 발급하지 말 것
def get_access_token() -> str:
    settings = _checked_settings()

    cached_token = _read_cached_token()
    if cached_token:
        return cached_token

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
    settings = _checked_settings()
    return _get_with_retry(
        f"{settings.kis_base_url}{_INDEX_PRICE_ENDPOINT}",
        headers=_headers(settings, _INDEX_PRICE_TR_ID),
        params={
            "FID_COND_MRKT_DIV_CODE": market_div_code,
            "FID_INPUT_ISCD": index_code,
        },
    )


# 해외 지수/환율 현재가 조회
# symbol로 대상 변경 가능 - S&P500="SPX", 나스닥="COMP", 니케이="JP#NI225", 달러환율="FX@KRW"
# market_div_code는 지수면 "N", 환율이면 "X"
def get_overseas_index_or_fx_price(market_div_code: str, symbol: str) -> dict:
    settings = _checked_settings()
    return _get_with_retry(
        f"{settings.kis_base_url}{_OVERSEAS_INDEX_PRICE_ENDPOINT}",
        headers=_headers(settings, _OVERSEAS_INDEX_PRICE_TR_ID),
        params={
            "FID_COND_MRKT_DIV_CODE": market_div_code,
            "FID_INPUT_ISCD": symbol,
            "FID_HOUR_CLS_CODE": "0",
            "FID_PW_DATA_INCU_YN": "N",
        },
    )


# 국내 업종 목록 조회 (한 시장의 업종 전체를 지수·등락률과 함께 한 번에 가져온다)
# market_cls_code로 시장 변경 - 코스피="K", 코스닥="Q"
#
# 주의 1. 등락률 순으로 정렬돼서 오지 않는다. 업종코드 순서로 오므로 정렬은 받는 쪽에서 해야 한다.
# 주의 2. 코스닥("Q")은 업종이 아니라 레버리지·인버스 같은 파생지수가 섞여서 온다(실제 호출로 확인).
#         그래서 주도 섹터는 코스피만 쓴다.
# 주의 3. 코스피도 38행 중에 "종합", "대형주", "제조" 같은 업종 아닌 것들이 섞여 있다.
#         쓸 업종만 고르는 목록은 leading_sector_service.py의 KOSPI_SECTOR_CODES에 있다.
#
# 응답 output2의 각 행: bstp_cls_code(업종코드) / hts_kor_isnm(업종명) / bstp_nmix_prdy_ctrt(등락률)
def get_index_category_price(market_cls_code: str = "K", index_code: str = "0001") -> dict:
    settings = _checked_settings()
    return _get_with_retry(
        f"{settings.kis_base_url}{_INDEX_CATEGORY_ENDPOINT}",
        headers=_headers(settings, _INDEX_CATEGORY_TR_ID),
        params={
            "FID_COND_MRKT_DIV_CODE": "U",
            "FID_INPUT_ISCD": index_code,
            "FID_COND_SCR_DIV_CODE": "20214",
            "FID_MRKT_CLS_CODE": market_cls_code,
            "FID_BLNG_CLS_CODE": "0",
        },
    )


# 등락률 순위 조회 (업종 내 상승 1위 종목, 애프터마켓 급상승 종목을 뽑는 데 사용)
# sector_code에 업종코드를 넣으면 그 업종 안에서만 순위가 나온다 - "0000"이면 시장 전체
# FID_RANK_SORT_CLS_CODE "0" = 상승률순, "1"로 바꾸면 하락률순이 된다
#
# market_div_code로 어느 시장을 볼지 정한다
#   "J"  거래소(KRX). 정규장 09:00~15:30에만 값이 움직이고 마감 후에는 종가에 멈춘다
#   "NX" 넥스트레이드(NXT). 프리마켓 08:00~08:50, 애프터마켓 15:40~20:00에도 계속 거래된다
#        17:30 / 20:00 슬롯의 급상승 종목은 이 값으로 뽑는다 (실측으로 10분 만에 순위가 바뀌는 것 확인)
#   "UN" 통합(J+NX)
#
# 아래 나머지 파라미터는 KIS가 요구하는 필수값인데 전부 "조건 없음/전체"를 뜻하는 고정값이라 여기 박아뒀다
# ("0"*9, "0"*10은 자릿수만큼 0을 채우라는 뜻으로, 대상 종목을 제한하지 않겠다는 의미)
#
# 응답 output의 각 행: hts_kor_isnm(종목명) / prdy_ctrt(등락률) / stck_shrn_iscd(종목코드)
def get_fluctuation_ranking(sector_code: str = "0000", market_div_code: str = "J") -> dict:
    settings = _checked_settings()
    return _get_with_retry(
        f"{settings.kis_base_url}{_FLUCTUATION_RANK_ENDPOINT}",
        headers=_headers(settings, _FLUCTUATION_RANK_TR_ID),
        params={
            "FID_COND_MRKT_DIV_CODE": market_div_code,
            "FID_COND_SCR_DIV_CODE": "20170",
            "FID_INPUT_ISCD": sector_code,
            "FID_RANK_SORT_CLS_CODE": "0",
            "FID_INPUT_CNT_1": "0",
            "FID_PRC_CLS_CODE": "0",
            "FID_INPUT_PRICE_1": "",
            "FID_INPUT_PRICE_2": "",
            "FID_VOL_CNT": "",
            "FID_TRGT_CLS_CODE": "0" * 9,
            "FID_TRGT_EXLS_CLS_CODE": "0" * 10,
            "FID_DIV_CLS_CODE": "0",
            "FID_RSFL_RATE1": "",
            "FID_RSFL_RATE2": "",
        },
    )


# 거래대금 순위 조회 (업종 내 거래 1위 종목을 뽑는 데 사용)
# sector_code 사용법은 위 등락률 순위와 같다
# FID_BLNG_CLS_CODE "3" = 거래금액순. "0"으로 바꾸면 거래량순이 된다
#
# 응답 output의 각 행: hts_kor_isnm(종목명) / prdy_ctrt(등락률) / mksc_shrn_iscd(종목코드)
# 주의: 종목코드 필드명이 등락률 순위(stck_shrn_iscd)와 다르다. 두 응답을 같은 코드로 처리하면 KeyError가 난다
def get_volume_ranking(sector_code: str = "0000") -> dict:
    settings = _checked_settings()
    return _get_with_retry(
        f"{settings.kis_base_url}{_VOLUME_RANK_ENDPOINT}",
        headers=_headers(settings, _VOLUME_RANK_TR_ID),
        params={
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_COND_SCR_DIV_CODE": "20171",
            "FID_INPUT_ISCD": sector_code,
            "FID_DIV_CLS_CODE": "0",
            "FID_BLNG_CLS_CODE": "3",
            "FID_TRGT_CLS_CODE": "0" * 9,
            "FID_TRGT_EXLS_CLS_CODE": "0" * 10,
            "FID_INPUT_PRICE_1": "",
            "FID_INPUT_PRICE_2": "",
            "FID_VOL_CNT": "",
            "FID_INPUT_DATE_1": "",
        },
    )


# 국내 업종 지수의 최근 체결 내역 조회 (지수가 언제 마지막으로 움직였는지 확인하는 데 사용)
# index_code로 지수 변경 - 코스피 종합="0001", 개별 업종은 업종코드를 넣으면 된다
#
# 지금 시점부터 거슬러 올라가며 최근 100틱만 준다. 과거 특정 시각을 지정해서는 못 가져온다
# (FID_INPUT_HOUR_1에 "170000" 같은 시각을 넣어도 무시되고 빈 배열이 온다 - 확인 완료)
# interval_seconds는 틱 간격(초). "60"이면 1분 간격, "30"이면 30초 간격
#
# 응답 output의 각 행: bsop_hour(체결시각 HHMMSS) / bstp_nmix_prpr(지수) / bstp_nmix_prdy_ctrt(등락률)
def get_index_tick_price(index_code: str = "0001", interval_seconds: str = "60") -> dict:
    settings = _checked_settings()
    return _get_with_retry(
        f"{settings.kis_base_url}{_INDEX_TICK_PRICE_ENDPOINT}",
        headers=_headers(settings, _INDEX_TICK_PRICE_TR_ID),
        params={
            "FID_COND_MRKT_DIV_CODE": "U",
            "FID_INPUT_ISCD": index_code,
            "FID_INPUT_HOUR_1": interval_seconds,
        },
    )


# 국내 휴장일 조회 (기준일부터 앞으로 며칠치를 한 번에 준다)
# base_date: "20260910" 형태의 기준일
#
# 응답 output의 각 행: bass_dt(날짜) / opnd_yn(개장일 여부 Y/N) / bzdy_yn(영업일) / tr_day_yn(거래일)
# 우리가 볼 값은 opnd_yn 하나다. 주말이든 공휴일이든 장이 안 서는 날은 전부 "N"으로 온다.
# 거래소가 정한 실제 휴장일이라 공휴일 달력보다 정확하다(임시공휴일·대체공휴일도 반영됨).
#
# 한 번에 20여 일치가 오므로 매번 부를 필요가 없다. 호출부에서 캐시해서 쓸 것
def get_holiday_calendar(base_date: str) -> dict:
    settings = _checked_settings()
    return _get_with_retry(
        f"{settings.kis_base_url}{_HOLIDAY_ENDPOINT}",
        headers=_headers(settings, _HOLIDAY_TR_ID),
        params={"BASS_DT": base_date, "CTX_AREA_NK": "", "CTX_AREA_FK": ""},
    )


# 예상체결 상승/하락 순위 조회 (08:30 슬롯의 급상승 종목을 뽑는 데 사용)
#
# 08:30~09:00은 KRX 장전 동시호가 시간이라 이 시간대의 "예상 체결"이 잡힌다.
# 정규장 밖이라 업종 지수는 안 도는데 이 값은 살아 있어서, 주도 섹터 대신 쓴다.
#
# market_open_code로 어느 동시호가를 볼지 정한다
#   "0" 장전예상 (08:30~09:00)
#   "1" 장마감예상 (15:20~15:30)
# rank_sort_code: 0:상승률 1:상승폭 2:보합 3:하락율 4:하락폭 5:체결량 6:거래대금
#
# 장전예상 값은 그날 하루 종일 남아 있다(오후에 호출해도 아침 값이 나온다 - 실측 확인).
# 08:30에 서버가 꺼져 있었어도 나중에 채울 수 있다는 뜻이다.
#
# 응답 output의 각 행: hts_kor_isnm(종목명) / prdy_ctrt(등락률) / stck_prpr(예상체결가)
#                     stck_sdpr(기준가) / cntg_vol(예상체결량) / antc_tr_pbmn(예상거래대금)
def get_expected_ranking(market_open_code: str = "0", rank_sort_code: str = "0", market_code: str = "0000") -> dict:
    settings = _checked_settings()
    return _get_with_retry(
        f"{settings.kis_base_url}{_EXPECTED_RANK_ENDPOINT}",
        headers=_headers(settings, _EXPECTED_RANK_TR_ID),
        params={
            "fid_rank_sort_cls_code": rank_sort_code,
            "fid_cond_mrkt_div_code": "J",
            "fid_cond_scr_div_code": "20182",
            "fid_input_iscd": market_code,
            "fid_div_cls_code": "0",
            "fid_aply_rang_prc_1": "",
            "fid_vol_cnt": "",
            "fid_pbmn": "",
            "fid_blng_cls_code": "0",
            "fid_mkop_cls_code": market_open_code,
        },
    )
