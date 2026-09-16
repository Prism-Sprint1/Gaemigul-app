# kis_client.py
# 한국투자증권(KIS) API 호출 (전 도메인 공용). 토큰 발급·캐싱, 재시도, 시세·순위·휴장일·투자자 매매동향·기간별 시세 조회, 종목 마스터 파일.
# 토큰은 계좌 단위라 KIS 호출은 반드시 이 파일을 거친다 (토큰을 새로 발급할 때마다 계좌 주인에게 알림이 간다).

from __future__ import annotations

import io
import json
import threading
import time
import zipfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx

from backend.core.config import get_settings

# 토큰 캐시 파일 위치: backend/.cache/kis_token.json (git에 올리지 않는다)
_TOKEN_CACHE_PATH = Path(__file__).resolve().parents[3] / ".cache" / "kis_token.json"

# KIS API별 주소(_ENDPOINT)와 거래 ID(_TR_ID). 아래 조회 함수들이 이 두 값으로 요청을 보낸다
#   ENDPOINT  kis_base_url 뒤에 붙는 경로
#   TR_ID     요청 헤더 tr_id에 넣는 코드. KIS가 이 값으로 어떤 조회인지 구분한다 (주소가 같아도 TR_ID가 다르면 다른 API)
# 값은 KIS 개발자 문서에 적힌 그대로다. 임의로 바꾸면 에러가 난다
# API를 추가하려면 두 줄을 추가하고, 함수에서 _get_with_retry(주소, headers=_headers(settings, TR_ID), params=...)로 부른다
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
_HOLIDAY_ENDPOINT = "/uapi/domestic-stock/v1/quotations/chk-holiday"
_HOLIDAY_TR_ID = "CTCA0903R"
_EXPECTED_RANK_ENDPOINT = "/uapi/domestic-stock/v1/ranking/exp-trans-updown"
_EXPECTED_RANK_TR_ID = "FHPST01820000"
_INVESTOR_DAILY_ENDPOINT = "/uapi/domestic-stock/v1/quotations/inquire-investor-daily-by-market"
_INVESTOR_DAILY_TR_ID = "FHPTJ04040000"
_INDEX_DAILY_ENDPOINT = "/uapi/domestic-stock/v1/quotations/inquire-index-daily-price"
_INDEX_DAILY_TR_ID = "FHPUP02120000"
_OVERSEAS_PERIOD_ENDPOINT = "/uapi/overseas-price/v1/quotations/inquire-daily-chartprice"
_OVERSEAS_PERIOD_TR_ID = "FHKST03030100"
_ITEM_PERIOD_ENDPOINT = "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
_ITEM_PERIOD_TR_ID = "FHKST03010100"

# 코스피 종목 마스터 파일 (KIS 공개 배포 주소. 토큰이 필요 없고 매일 갱신된다)
_KOSPI_MASTER_URL = "https://new.real.download.dws.co.kr/common/master/kospi_code.mst.zip"
_KOSPI_MASTER_FILE = "kospi_code.mst"

# 조회 실패 시 재시도 횟수, 대기(초, 시도마다 배수로 늘어남), 요청 타임아웃(초)
_RETRY_COUNT = 3
_RETRY_WAIT_SECONDS = 0.5
_TIMEOUT_SECONDS = 10.0

# 토큰 발급 잠금. 지표 바·히트맵 수집이 동시에 시작돼도 발급은 한 번만 한다
_TOKEN_LOCK = threading.Lock()


# 캐시된 토큰 (없거나 만료됐으면 None). 중간에 끊긴 쓰기·옛 형식 캐시도 None으로 보고 새로 발급한다
def _read_cached_token() -> str | None:
    if not _TOKEN_CACHE_PATH.exists():
        return None

    try:
        cached = json.loads(_TOKEN_CACHE_PATH.read_text(encoding="utf-8"))
        if cached["expires_at"] > time.time():
            return cached["access_token"]
    except (OSError, ValueError, KeyError, TypeError):
        return None
    return None


# 발급받은 토큰을 파일에 저장한다. 임시 파일에 쓴 뒤 바꿔치기해서 읽는 쪽이 반쯤 쓴 파일을 보지 않게 한다
def _write_cached_token(access_token: str, expires_in: int) -> None:
    _TOKEN_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = _TOKEN_CACHE_PATH.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(
            {
                "access_token": access_token,
                "expires_at": time.time() + expires_in - 60,  # 만료 60초 전부터는 새로 발급
            }
        ),
        encoding="utf-8",
    )
    temporary.replace(_TOKEN_CACHE_PATH)


# 키 설정을 확인하고 설정값을 돌려준다. 키가 없으면 RuntimeError
# 공개 함수는 모두 여기서 설정값을 받는다 (캐시된 토큰이 있어도 키 검사를 건너뛰지 않도록)
def _checked_settings():
    settings = get_settings()
    if not settings.kis_app_key or not settings.kis_app_secret:
        raise RuntimeError("KIS_APP_KEY / KIS_APP_SECRET가 .env에 없습니다. backend/.env에 추가해주세요.")
    return settings


# 조회 API 공통 헤더. API마다 tr_id만 다르다
def _headers(settings, tr_id: str) -> dict[str, str]:
    return {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {get_access_token()}",
        "appkey": settings.kis_app_key,
        "appsecret": settings.kis_app_secret,
        "tr_id": tr_id,
        "custtype": "P",
    }


# 조회 API 공통 GET (JSON 응답). 재시도 규칙은 _send_with_retry
def _get_with_retry(url: str, *, headers: dict, params: dict) -> dict:
    return _send_with_retry(url, headers=headers, params=params).json()


# GET을 보내고 응답을 돌려준다 (JSON 조회와 마스터 파일 다운로드가 같이 쓴다)
# 5xx(초당 한도 초과 EGW00201 포함)와 연결 오류는 _RETRY_COUNT번까지 재시도하고, 4xx는 바로 에러를 낸다
# 토큰 발급에는 쓰지 않는다 (재시도하면 알림이 여러 번 간다)
def _send_with_retry(url: str, *, headers: dict | None = None, params: dict | None = None) -> httpx.Response:
    last_error = None

    for attempt in range(_RETRY_COUNT):
        try:
            response = httpx.get(url, headers=headers, params=params, timeout=_TIMEOUT_SECONDS)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as error:
            if error.response.status_code < 500:
                raise
            last_error = error
        except httpx.TransportError as error:
            last_error = error

        if attempt < _RETRY_COUNT - 1:
            time.sleep(_RETRY_WAIT_SECONDS * (attempt + 1))

    raise last_error


# 접근 토큰. 캐시가 유효하면 재사용하고 없을 때만 새로 발급한다
# 토큰이 필요하면 반드시 이 함수를 쓴다 (따로 발급하면 계좌 주인에게 알림이 간다)
def get_access_token() -> str:
    settings = _checked_settings()

    with _TOKEN_LOCK:
        return _get_access_token_locked(settings)


def _get_access_token_locked(settings) -> str:
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


# 국내 지수 현재가 (지표 바의 코스피·코스닥)
# market_div_code "U"(업종), index_code 코스피 "0001" / 코스닥 "1001" / 개별 업종코드
# 응답 output: bstp_nmix_prpr(지수) / bstp_nmix_prdy_ctrt(전일 대비 등락률)
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


# 해외 지수·환율 현재가 (지표 바의 나스닥·S&P500·니케이·환율)
# market_div_code 지수 "N" / 환율 "X", symbol 나스닥 "COMP" / S&P500 "SPX" / 니케이 "JP#NI225" / 원달러 "FX@KRW"
# 응답 output1: ovrs_nmix_prpr(현재가) / prdy_ctrt(전일 대비 등락률)
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


# 업종 목록 (한 시장의 업종 지수·등락률 전체) - 주도 섹터에서 쓴다
# market_cls_code 코스피 "K" / 코스닥 "Q", index_code 코스피 "0001" / 코스닥 "1001"
# 주의: 업종코드 순으로 오고(정렬은 받는 쪽에서), 종합·대형주 같은 비업종이 섞여 온다
# 주의: 코스닥은 응답이 100행에서 잘리는데 호출마다 구성이 달라 순위용으로 쓸 수 없다 (코스피는 38행으로 일정)
# 응답 output2: bstp_cls_code(업종코드) / hts_kor_isnm(업종명) / bstp_nmix_prdy_ctrt(등락률)
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


# 등락률 순위 (상승률순 30개) - 두 곳에서 쓴다
#   주도 섹터의 업종 내 상승 1위        sector_code=업종코드, market_div_code="J"
#   정규장 밖 급상승 종목               sector_code="0000", market_div_code="NX"(08:30 프리마켓) / "J"(17:30·20:00 애프터마켓)
# sector_code: 업종코드면 그 업종 안에서, "0000"이면 시장 전체
# market_div_code: "J" 한국거래소(정규장 09:00~15:30, 애프터마켓 16:00~20:00) / "NX" 넥스트레이드(프리마켓 08:00~08:50, 애프터마켓 15:40~20:00)
#   "UN"(통합)은 이 순위 API에서 0행이 온다
# FID_PRC_CLS_CODE: "1" 전일 종가 대비(prdy_ctrt 순) / "0" 당일 저가 대비(lwpr_vrss_prpr_rate 순 - 화면 등락률과 순서가 다르고 진짜 상위 종목이 30개 밖으로 밀린다)
# 응답 output: hts_kor_isnm(종목명) / prdy_ctrt(등락률) / stck_prpr(현재가) / stck_shrn_iscd(종목코드)
def get_fluctuation_ranking(sector_code: str = "0000", market_div_code: str = "J") -> dict:
    settings = _checked_settings()
    return _get_with_retry(
        f"{settings.kis_base_url}{_FLUCTUATION_RANK_ENDPOINT}",
        headers=_headers(settings, _FLUCTUATION_RANK_TR_ID),
        params={
            "FID_COND_MRKT_DIV_CODE": market_div_code,
            "FID_COND_SCR_DIV_CODE": "20170",
            "FID_INPUT_ISCD": sector_code,
            "FID_RANK_SORT_CLS_CODE": "0",  # 상승률순
            "FID_INPUT_CNT_1": "0",
            "FID_PRC_CLS_CODE": "1",  # 전일 종가 대비 등락률 순
            "FID_INPUT_PRICE_1": "",
            "FID_INPUT_PRICE_2": "",
            "FID_VOL_CNT": "",
            "FID_TRGT_CLS_CODE": "0" * 9,  # 대상 제한 없음
            "FID_TRGT_EXLS_CLS_CODE": "0" * 10,  # 제외 대상 없음
            "FID_DIV_CLS_CODE": "0",
            "FID_RSFL_RATE1": "",
            "FID_RSFL_RATE2": "",
        },
    )


# 거래 순위 - 주도 섹터의 업종 내 "거래 1위"에 쓴다 (거래소 기준)
# sector_code: 업종코드 / "0000"(시장 전체)
# FID_BLNG_CLS_CODE: "3" 거래대금순(현재) / "0" 거래량순 / "1" 거래증가율 / "2" 거래회전율
# 응답 output: hts_kor_isnm(종목명) / prdy_ctrt(등락률) / mksc_shrn_iscd(종목코드 - 등락률 순위와 필드명이 다르다)
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


# 국내 휴장일 (기준일부터 20여 일치) - market_hours가 캐시해서 쓴다
# base_date: "20260914" 형태
# 응답 output: bass_dt(날짜) / opnd_yn(개장 여부 Y/N - 주말·공휴일·임시공휴일이면 N)
def get_holiday_calendar(base_date: str) -> dict:
    settings = _checked_settings()
    return _get_with_retry(
        f"{settings.kis_base_url}{_HOLIDAY_ENDPOINT}",
        headers=_headers(settings, _HOLIDAY_TR_ID),
        params={"BASS_DT": base_date, "CTX_AREA_NK": "", "CTX_AREA_FK": ""},
    )


# KRX 동시호가 예상체결 순위 - 08:30 급상승 종목의 대체 수단 (top_gainer_service.SOURCE_BY_SLOT이 "expected"일 때)
# market_open_code: "0" 장전예상(08:30~09:00) / "1" 장마감예상(15:20~15:30)
# rank_sort_code: 0 상승률 / 1 상승폭 / 2 보합 / 3 하락률 / 4 하락폭 / 5 체결량 / 6 거래대금
# 장전예상 값은 그날 하루 종일 조회된다 (놓친 08:30 슬롯을 나중에 채울 수 있다)
# 응답 output: hts_kor_isnm(종목명) / prdy_ctrt(등락률) / stck_prpr(예상체결가)
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


# 시장별 투자자 매매동향 (일별) - 보고서의 외국인·기관·개인 순매수, 차트 분기 외국인 합산에 쓴다
# base_date: "20260911" 형태. 이 날짜부터 거슬러 최근 300거래일이 온다 (더 이전은 base_date를 옮겨 다시 호출)
# market_code 코스피 "KSP" / 코스닥 "KSQ", index_code 코스피 "0001" / 코스닥 "1001"
# 날짜를 지정해 조회하므로 지난 날짜도 나중에 다시 받을 수 있다
# 응답 output (최신 날짜부터): stck_bsop_date(날짜) / frgn_ntby_tr_pbmn(외국인) / orgn_ntby_tr_pbmn(기관계) /
#   prsn_ntby_tr_pbmn(개인) 순매수 거래대금 - 단위 백만원, 음수면 순매도
def get_investor_daily_by_market(base_date: str, market_code: str = "KSP", index_code: str = "0001") -> dict:
    settings = _checked_settings()
    return _get_with_retry(
        f"{settings.kis_base_url}{_INVESTOR_DAILY_ENDPOINT}",
        headers=_headers(settings, _INVESTOR_DAILY_TR_ID),
        params={
            "FID_COND_MRKT_DIV_CODE": "U",
            "FID_INPUT_ISCD": index_code,
            "FID_INPUT_DATE_1": base_date,
            "FID_INPUT_ISCD_1": market_code,
            "FID_INPUT_DATE_2": base_date,  # 문서상 DATE_1과 같은 날짜를 넣는다
            "FID_INPUT_ISCD_2": index_code,
        },
    )


# 국내 업종 지수 일자별·주별 - 보고서의 섹터 카드, VKOSPI에 쓴다
# index_code: 업종코드 (VKOSPI "0503", 코스피 "0001"), base_date: "20260911" 형태
# period: "D" 일별 / "W" 주별 / "M" 월별
# 응답 output1 (현재 값 하나): bstp_nmix_prpr(지수) / bstp_nmix_prdy_ctrt(전일 대비 등락률) /
#   ascn_issu_cnt·down_issu_cnt·stnr_issu_cnt(상승·하락·보합 종목 수) / acml_tr_pbmn(거래대금) / prdy_tr_pbmn(전일 거래대금)
#   주의: output1은 base_date를 무시하고 항상 최근 거래일 값이다. 종목 수·전일 거래대금은 그날(다음 개장 전까지) 받아야 한다
# 응답 output2 (base_date부터 거슬러 최대 100행, 최신부터): stck_bsop_date(일별은 그날, 주별은 그 주 월요일) /
#   bstp_nmix_prpr(종가) / bstp_nmix_prdy_ctrt(직전 기간 대비 등락률) / acml_tr_pbmn(기간 거래대금)
#   종목 수는 output2에 없다
# 거래대금 단위는 백만원
def get_index_daily_price(index_code: str, base_date: str, period: str = "D") -> dict:
    settings = _checked_settings()
    return _get_with_retry(
        f"{settings.kis_base_url}{_INDEX_DAILY_ENDPOINT}",
        headers=_headers(settings, _INDEX_DAILY_TR_ID),
        params={
            "FID_COND_MRKT_DIV_CODE": "U",
            "FID_INPUT_ISCD": index_code,
            "FID_INPUT_DATE_1": base_date,
            "FID_PERIOD_DIV_CODE": period,
        },
    )


# 해외 지수·환율 기간별 시세 - 보고서 차트의 분기별 환율에 쓴다
# market_div_code 지수 "N" / 환율 "X", symbol 원달러 "FX@KRW" (심볼은 get_overseas_index_or_fx_price와 같다)
# start_date·end_date: "20260101" 형태, period: "D" 일 / "W" 주 / "M" 월 / "Y" 년
# 주의: 틀린 심볼도 rt_cd "0"으로 성공하고 값이 0이 온다. 받는 쪽에서 0 값을 걸러낼 것
# 응답 output2 (최신부터): stck_bsop_date(월별은 그달 1일) / ovrs_nmix_prpr(기간 마지막 값 = 종가)
def get_overseas_period_price(market_div_code: str, symbol: str, start_date: str, end_date: str, period: str = "D") -> dict:
    settings = _checked_settings()
    return _get_with_retry(
        f"{settings.kis_base_url}{_OVERSEAS_PERIOD_ENDPOINT}",
        headers=_headers(settings, _OVERSEAS_PERIOD_TR_ID),
        params={
            "FID_COND_MRKT_DIV_CODE": market_div_code,
            "FID_INPUT_ISCD": symbol,
            "FID_INPUT_DATE_1": start_date,
            "FID_INPUT_DATE_2": end_date,
            "FID_PERIOD_DIV_CODE": period,
        },
    )


# 국내 종목 기간별 시세 (일·주·월봉) - 주간 섹터 카드의 종목별 주간 상승·하락 판정에 쓴다
# stock_code: 종목코드 6자리, start_date·end_date: "20260801" 형태, period: "D" 일 / "W" 주 / "M" 월
# 응답 output2 (최신부터, 최대 100행): stck_bsop_date(주봉은 그 주 월요일) / stck_clpr(기간 종가) / prdy_vrss(직전 기간 대비 가격 차이)
#   주의: 주봉에는 등락률(prdy_ctrt) 칸이 없다. 오르내림은 prdy_vrss 부호나 종가 비교로 판단한다
def get_stock_period_price(stock_code: str, start_date: str, end_date: str, period: str = "D") -> dict:
    settings = _checked_settings()
    return _get_with_retry(
        f"{settings.kis_base_url}{_ITEM_PERIOD_ENDPOINT}",
        headers=_headers(settings, _ITEM_PERIOD_TR_ID),
        params={
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": stock_code,
            "FID_INPUT_DATE_1": start_date,
            "FID_INPUT_DATE_2": end_date,
            "FID_PERIOD_DIV_CODE": period,
            "FID_ORG_ADJ_PRC": "0",  # 수정주가 반영
        },
    )


# 코스피 종목 마스터 파일(kospi_code.mst) 내용을 바이트로 돌려준다 - 주간 섹터 카드의 업종 종목 명단에 쓴다
# zip(약 120KB)을 받아 압축을 풀기만 한다. 줄 형식 해석은 report_data_service._sector_members
def get_kospi_master() -> bytes:
    response = _send_with_retry(_KOSPI_MASTER_URL)
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        return archive.read(_KOSPI_MASTER_FILE)


# calendar 일정
# 1. 국내휴장일조회, 2.국내주식 종목추정실적, 3.배당일정, 4.주주총회일정, 5.합병/분할일정, 6.공모주청약일정

_KSD_DIVIDEND_ENDPOINT = "/uapi/domestic-stock/v1/ksdinfo/dividend"
_KSD_DIVIDEND_TR_ID = "HHKDB669102C0"


# 예탁원정보(배당일정) 조회. sht_cd를 주면 그 종목만, 비워두면 전체(페이지당 최대 100건, 연속조회
# 미구현이라 전체조회 시 일부만 옴 - 종목코드를 지정해서 쓰는 걸 권장)
# gb1: "0"=배당전체(기본값), "1"=결산배당, "2"=중간배당
def get_dividend_schedule(f_dt: str, t_dt: str, *, sht_cd: str = "", gb1: str = "0") -> list[dict]:
    settings = get_settings()
    response = httpx.get(
        f"{settings.kis_base_url}{_KSD_DIVIDEND_ENDPOINT}",
        headers={
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {get_access_token()}",
            "appkey": settings.kis_app_key,
            "appsecret": settings.kis_app_secret,
            "tr_id": _KSD_DIVIDEND_TR_ID,
            "custtype": "P",
        },
        params={
            "CTS": "",
            "GB1": gb1,
            "F_DT": f_dt,
            "T_DT": t_dt,
            "SHT_CD": sht_cd,
            "HIGH_GB": "",
        },
    )
    response.raise_for_status()
    body = response.json()
    return body.get("output1") or []


_KSD_PUB_OFFER_ENDPOINT = "/uapi/domestic-stock/v1/ksdinfo/pub-offer"
_KSD_PUB_OFFER_TR_ID = "HHKDB669108C0"


# 예탁원정보(공모주청약일정, IPO) 조회. sht_cd를 비워두면 전체 시장(1년치가 100건 미만이라
# 페이지 제한에 안 걸림 - 실제 라이브 호출로 확인함)
def get_ipo_schedule(f_dt: str, t_dt: str, *, sht_cd: str = "") -> list[dict]:
    settings = get_settings()
    response = httpx.get(
        f"{settings.kis_base_url}{_KSD_PUB_OFFER_ENDPOINT}",
        headers={
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {get_access_token()}",
            "appkey": settings.kis_app_key,
            "appsecret": settings.kis_app_secret,
            "tr_id": _KSD_PUB_OFFER_TR_ID,
            "custtype": "P",
        },
        params={"SHT_CD": sht_cd, "CTS": "", "F_DT": f_dt, "T_DT": t_dt},
    )
    response.raise_for_status()
    body = response.json()
    return body.get("output1") or []


_KSD_PAIDIN_CAPIN_ENDPOINT = "/uapi/domestic-stock/v1/ksdinfo/paidin-capin"
_KSD_PAIDIN_CAPIN_TR_ID = "HHKDB669100C0"


# 예탁원정보(유상증자일정) 조회. gb1: "1"=청약일별(기본값), "2"=기준일별.
# sht_cd 비워두면 전체 시장(1년치가 100건 미만이라 페이지 제한에 안 걸림)
def get_paidin_capital_increase_schedule(
    f_dt: str, t_dt: str, *, sht_cd: str = "", gb1: str = "1"
) -> list[dict]:
    settings = get_settings()
    response = httpx.get(
        f"{settings.kis_base_url}{_KSD_PAIDIN_CAPIN_ENDPOINT}",
        headers={
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {get_access_token()}",
            "appkey": settings.kis_app_key,
            "appsecret": settings.kis_app_secret,
            "tr_id": _KSD_PAIDIN_CAPIN_TR_ID,
            "custtype": "P",
        },
        params={"CTS": "", "GB1": gb1, "F_DT": f_dt, "T_DT": t_dt, "SHT_CD": sht_cd},
    )
    response.raise_for_status()
    body = response.json()
    return body.get("output1") or []


_KSD_BONUS_ISSUE_ENDPOINT = "/uapi/domestic-stock/v1/ksdinfo/bonus-issue"
_KSD_BONUS_ISSUE_TR_ID = "HHKDB669101C0"


# 예탁원정보(무상증자일정) 조회. 전체 시장 조회 시 1년치가 100건에 걸릴 수 있어(실제 확인함)
# sht_cd로 종목을 지정해서 쓰는 걸 권장
def get_bonus_issue_schedule(f_dt: str, t_dt: str, *, sht_cd: str = "") -> list[dict]:
    settings = get_settings()
    response = httpx.get(
        f"{settings.kis_base_url}{_KSD_BONUS_ISSUE_ENDPOINT}",
        headers={
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {get_access_token()}",
            "appkey": settings.kis_app_key,
            "appsecret": settings.kis_app_secret,
            "tr_id": _KSD_BONUS_ISSUE_TR_ID,
            "custtype": "P",
        },
        params={"CTS": "", "F_DT": f_dt, "T_DT": t_dt, "SHT_CD": sht_cd},
    )
    response.raise_for_status()
    body = response.json()
    return body.get("output1") or []


_KSD_MERGER_SPLIT_ENDPOINT = "/uapi/domestic-stock/v1/ksdinfo/merger-split"
_KSD_MERGER_SPLIT_TR_ID = "HHKDB669104C0"


# 예탁원정보(합병_분할일정) 조회. sht_cd를 비워두면 전체 시장 대상(1년치가 30건 안팎이라
# 배당일정과 달리 페이지 제한에 안 걸림 - 실제 라이브 호출로 확인함)
def get_merger_split_schedule(f_dt: str, t_dt: str, *, sht_cd: str = "") -> list[dict]:
    settings = get_settings()
    response = httpx.get(
        f"{settings.kis_base_url}{_KSD_MERGER_SPLIT_ENDPOINT}",
        headers={
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {get_access_token()}",
            "appkey": settings.kis_app_key,
            "appsecret": settings.kis_app_secret,
            "tr_id": _KSD_MERGER_SPLIT_TR_ID,
            "custtype": "P",
        },
        params={
            "CTS": "",
            "F_DT": f_dt,
            "T_DT": t_dt,
            "SHT_CD": sht_cd,
        },
    )
    response.raise_for_status()
    body = response.json()
    return body.get("output1") or []


# ---------------------------------------------------------------------------
# heatmap 도메인용 공용 요청 (히트맵 담당 작성)
# ---------------------------------------------------------------------------

_REQUEST_LOCK = threading.Lock()
_LAST_REQUEST_AT = 0.0
_HTTP = httpx.Client(timeout=httpx.Timeout(20.0, connect=10.0))
_MASTER_CACHE_PATH = _TOKEN_CACHE_PATH.parent / "heatmap" / "masters"


class KISAPIError(RuntimeError):
    """HTTP 200이어도 KIS 업무 응답(rt_cd)이 실패이면 수집을 중단한다."""


def _wait_for_request_slot() -> None:
    # timeline과 heatmap의 호출을 함께 제한한다. 서버는 스케줄러 1개/worker 1개로 운영.
    global _LAST_REQUEST_AT
    with _REQUEST_LOCK:
        interval = 1.0 / get_settings().heatmap_requests_per_second
        delay = interval - (time.monotonic() - _LAST_REQUEST_AT)
        if delay > 0:
            time.sleep(delay)
        _LAST_REQUEST_AT = time.monotonic()


def _get(endpoint: str, tr_id: str, params: dict[str, str]) -> dict:
    """공용 토큰, 연결 재사용, 속도 제한, 일시적 장애 재시도를 거치는 읽기 전용 GET."""
    settings = get_settings()
    for attempt in range(3):
        _wait_for_request_slot()
        try:
            response = _HTTP.get(
                f"{settings.kis_base_url}{endpoint}",
                headers={
                    "content-type": "application/json; charset=utf-8",
                    "authorization": f"Bearer {get_access_token()}",
                    "appkey": settings.kis_app_key,
                    "appsecret": settings.kis_app_secret,
                    "tr_id": tr_id,
                    "custtype": "P",
                },
                params=params,
            )
            if response.status_code in (429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(0.5 * 2**attempt)
                continue
            response.raise_for_status()
            body = response.json()
            if body.get("rt_cd", "0") != "0":
                # 초당 호출 제한은 HTTP 200의 업무 오류로도 전달된다.
                if body.get("msg_cd") == "EGW00201" and attempt < 2:
                    time.sleep(0.5 * 2**attempt)
                    continue
                raise KISAPIError(f"KIS {tr_id}: {body.get('msg_cd', 'unknown')}")
            return body
        except httpx.TransportError:
            if attempt == 2:
                raise
            time.sleep(0.5 * 2**attempt)
    raise KISAPIError(f"KIS {tr_id}: retry exhausted")


# ---------------------------------------------------------------------------
# 히트맵용 KIS 요청 양식
# 공식 예제: https://github.com/koreainvestment/open-trading-api/tree/main/examples_llm/domestic_stock
# 모든 금액/수량의 화면용 변환과 기간 집계는 domain/heatmap/services에서 관리한다.
# 일간 누적 거래량은 10분마다 새 값으로 교체한다(누적값끼리 더하지 않는다).
# ---------------------------------------------------------------------------


def get_sector_prices(market: str) -> dict:
    # 국내업종 구분별전체시세 [국내주식-066], 실전 TR: FHPUP02140000
    # 요청: U=업종, 0001/K=KOSPI, 1001/Q=KOSDAQ, 화면20214, 소속0=전체.
    # output2: bstp_cls_code(업종코드), hts_kor_isnm(업종명), acml_vol(누적거래량),
    # acml_tr_pbmn(누적거래대금), acml_vol_rlim(거래량 비중), bstp_nmix_prdy_ctrt(%).
    # 이 API는 '1위 업종' 전용 API가 아니며 종합/규모별 지수도 포함한다.
    # 히트맵 순위는 종목마스터의 최하위 업종으로 묶은 보통주 거래량(주)을 합산한다.
    # 지수 원본 거래량 단위와 종목별 거래량을 섞어 합산하지 않는다.
    _validate_market(market)
    return _get("/uapi/domestic-stock/v1/quotations/inquire-index-category-price", "FHPUP02140000", {
        "FID_COND_MRKT_DIV_CODE": "U",
        "FID_INPUT_ISCD": "0001" if market == "kospi" else "1001",
        "FID_COND_SCR_DIV_CODE": "20214",
        "FID_MRKT_CLS_CODE": "K" if market == "kospi" else "Q",
        "FID_BLNG_CLS_CODE": "0",
    })


def get_stock_quotes(codes: list[str]) -> dict:
    # 관심종목(멀티종목) 시세조회 [국내주식-205], TR FHKST11300006, 최대30종목.
    # 그룹 등록 없이 종목코드 직접 전달. J=KRX 정규시장(NX=NXT는 이번 범위 제외).
    # output: inter_shrn_iscd(코드), inter2_prpr(현재가/원), prdy_ctrt(전일대비%),
    # acml_vol(당일누적/주), acml_tr_pbmn(당일누적/원), inter2_prdy_clpr(전일종가/원).
    # 시가총액 필드는 없다. 마스터 상장주수/기간시세의 정확한 상장주수와 가격을 사용한다.
    if not 1 <= len(codes) <= 30:
        raise ValueError("복수시세 조회는 1~30종목씩 요청해야 합니다.")
    params = {}
    for index, code in enumerate(codes, 1):
        _validate_stock_code(code)
        params[f"FID_COND_MRKT_DIV_CODE_{index}"] = "J"
        params[f"FID_INPUT_ISCD_{index}"] = code
    return _get("/uapi/domestic-stock/v1/quotations/intstock-multprice", "FHKST11300006", params)


def get_stock_history(code: str, start_date: str, end_date: str) -> dict:
    # 국내주식기간별시세 [국내주식-016], TR FHKST03010100, 최대100개 봉.
    # 요청 날짜 YYYYMMDD, D=일봉, 수정주가0(액면분할 등 반영).
    # 주간/월간은 일봉의 해당 주/월 시작 전 마지막 종가를 기준으로 서비스에서 계산.
    # output2: stck_bsop_date(거래일), stck_clpr(수정종가/원), acml_vol(그날 거래량/주).
    # output1: lstn_stcn(정확한 상장주수/주), hts_avls(시가총액/억원).
    _validate_stock_code(code)
    start, end = datetime.strptime(start_date, "%Y%m%d"), datetime.strptime(end_date, "%Y%m%d")
    if not 0 <= (end - start).days <= 99:
        raise ValueError("일봉 요청은 시작일부터 최대100일 이내로 나누어야 합니다.")
    return _get("/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice", "FHKST03010100", {
        "FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code,
        "FID_INPUT_DATE_1": start_date, "FID_INPUT_DATE_2": end_date,
        "FID_PERIOD_DIV_CODE": "D", "FID_ORG_ADJ_PRC": "0",
    })


def get_market_calendar(base_date: str) -> dict:
    # 국내휴장일조회 [국내주식-040], TR CTCA0903R.
    # output: bass_dt(YYYYMMDD), opnd_yn(Y=개장), bzdy_yn(영업일), tr_day_yn(거래일).
    # KIS 권고: 원장 서비스 보호를 위해 가급적1일1회 호출. 도메인에서 일별로 캐싱한다.
    # 개장 여부만 제공하므로 수능일 등 특수 개장시각은 HEATMAP_SESSION_OVERRIDES로 보완.
    datetime.strptime(base_date, "%Y%m%d")
    return _get("/uapi/domestic-stock/v1/quotations/chk-holiday", "CTCA0903R", {
        "BASS_DT": base_date, "CTX_AREA_FK": "", "CTX_AREA_NK": "",
    })


def get_stock_info(code: str) -> dict:
    # 주식기본조회 [국내주식-067], TR CTPF1002R, 300=주식 상품.
    # output: scts_mket_lstg_abol_dt/KOSDAQ는 kosdaq_mket_lstg_abol_dt(상장폐지일 YYYYMMDD),
    # idx_bztp_lcls/mcls/scls_cd(업종), tr_stop_yn(거래정지), lstg_stqt(상장주수).
    # 마스터에 기준가/시가총액이 모두0인 종목만 추가 확인하여 폐지 종목의 잔존 레코드를 거른다.
    # 가격 미제공만으로 상장폐지라고 추정하지 않는다.
    _validate_stock_code(code)
    return _get("/uapi/domestic-stock/v1/quotations/search-stock-info", "CTPF1002R", {
        "PRDT_TYPE_CD": "300", "PDNO": code,
    })


def _validate_market(market: str) -> None:
    if market not in ("kospi", "kosdaq"):
        raise ValueError("지원 시장은 kospi, kosdaq입니다.")


def _validate_stock_code(code: str) -> None:
    if len(code) != 6 or not code.isascii() or not code.isalnum():
        raise ValueError("종목코드는 6자리 영문/숫자여야 합니다.")


def _download_master(name: str) -> str:
    # KIS 공식 종목정보파일, 인증 없이 제공. ZIP 파일을 디스크에 풀지 않고 지정 파일만 읽는다.
    response = _HTTP.get(f"https://new.real.download.dws.co.kr/common/master/{name}.mst.zip")
    response.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        info = archive.getinfo(f"{name}.mst")
        if info.file_size > 20_000_000:
            raise ValueError("종목정보파일 크기가 예상 범위를 초과했습니다.")
        return archive.read(info).decode("cp949")


def _read_master_cache(name: str):
    path = _MASTER_CACHE_PATH / f"{name}.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data["date"] == datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat():
            return data["items"]
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return None


def _write_master_cache(name: str, items) -> None:
    _MASTER_CACHE_PATH.mkdir(parents=True, exist_ok=True)
    path = _MASTER_CACHE_PATH / f"{name}.json"
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps({"date": datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat(), "items": items}, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def get_sector_master() -> dict[str, str]:
    # idxcode.mst: 시장구분1자리 + 업종코드4자리 + 업종명. 최신 명칭을 매일 읽어온다.
    # 공식 형식: stocks_info/업종코드정보.h 및 sector_code.py (명칭은 코드 뒤에서 읽음).
    cached = _read_master_cache("sectors")
    if cached is not None:
        return cached
    items = {}
    for row in _download_master("idxcode").splitlines():
        code, name = row[1:5], row[5:].strip()
        if len(code) == 4 and code.isdigit() and name:
            items[code] = name
    if not items:
        raise ValueError("KIS 업종정보파일에 업종이 없습니다.")
    _write_master_cache("sectors", items)
    return items


def _parse_stock_master(contents: str, market: str) -> list[dict]:
    # KIS 공식 stocks_info/종목마스터정보(코스피).h, (코스닥).h의 고정폭 형식.
    # 공식 Python 예제의 꼬리228/222자는 줄바꿈을 포함한다. splitlines 후227/221자.
    # 공통 앞쪽: 그룹[0:2], 업종 대/중/소[3:7],[7:11],[11:15].
    # ST=주권, FS=외국주권만 포함. 우선주, SPAC, ETF/ETN, DR 등 별도 상품은 제외.
    # 상장주수 원본은 천주, 시가총액 원본은 억원 -> 각각 주/원으로 정규화.
    _validate_market(market)
    kospi = market == "kospi"
    tail_length = 227 if kospi else 221
    spac_offset, preferred_offset = (29, 158) if kospi else (24, 153)
    shares_offset, cap_offset = (113, 212) if kospi else (108, 206)
    reference_offset, suspended_offset = (41, 60) if kospi else (36, 55)
    items = []
    for row in contents.splitlines():
        if len(row) < tail_length + 22:
            continue
        head, fields = row[:-tail_length], row[-tail_length:]
        code = head[:9].strip()
        if fields[:2] not in ("ST", "FS") or fields[preferred_offset] != "0" or fields[spac_offset] == "Y":
            continue
        if len(code) != 6 or not code.isascii() or not code.isalnum():
            continue
        sector_codes = [fields[offset:offset + 4] for offset in (3, 7, 11) if fields[offset:offset + 4].isdigit() and fields[offset:offset + 4] != "0000"]
        def number(start: int, width: int) -> int:
            return int(fields[start:start + width].strip() or "0")
        items.append({
            "code": code, "name": head[21:].strip(),
            "sector_code": sector_codes[-1] if sector_codes else "unclassified",
            "sector_codes": sector_codes,
            "market_cap": number(cap_offset, 9) * 100_000_000,
            "listed_shares": number(shares_offset, 15) * 1000,
            "reference_price": number(reference_offset, 9),
            "suspended": fields[suspended_offset] == "Y",
        })
    if not items:
        raise ValueError(f"KIS {market} 종목정보파일에서 보통주를 읽지 못했습니다.")
    return items


def get_stock_master(market: str) -> list[dict]:
    _validate_market(market)
    cached = _read_master_cache(market)
    if cached is not None:
        return cached
    items = _parse_stock_master(_download_master(f"{market}_code"), market)
    _write_master_cache(market, items)
    return items
# 국내선물옵션 - 46번 사전조사에서 실제 라이브 호출로 확인한 API들을 client 함수로 승격.
# 인증은 기존 get_access_token()을 그대로 재사용한다(새 인증 코드 없음).

_FUTOPT_OPTION_LIST_ENDPOINT = "/uapi/domestic-futureoption/v1/quotations/display-board-option-list"
_FUTOPT_OPTION_LIST_TR_ID = "FHPIO056104C0"


# 국내옵션전광판_옵션월물리스트[국내선물-020] - 만기 "년월"만 준다(mtrt_yymm_code/mtrt_yymm).
# 정확한 만기일은 없다 - get_price()로 종목별 futs_last_tr_date를 따로 조회해야 한다.
def get_option_month_list(fid_cond_scr_div_code: str = "509") -> list[dict]:
    settings = get_settings()
    response = httpx.get(
        f"{settings.kis_base_url}{_FUTOPT_OPTION_LIST_ENDPOINT}",
        headers={
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {get_access_token()}",
            "appkey": settings.kis_app_key,
            "appsecret": settings.kis_app_secret,
            "tr_id": _FUTOPT_OPTION_LIST_TR_ID,
            "custtype": "P",
        },
        params={
            "FID_COND_SCR_DIV_CODE": fid_cond_scr_div_code,
            "FID_COND_MRKT_DIV_CODE": "",
            "FID_COND_MRKT_CLS_CODE": "",
        },
    )
    response.raise_for_status()
    body = response.json()
    return body.get("output") or []


_FUTOPT_FUTURES_BOARD_ENDPOINT = "/uapi/domestic-futureoption/v1/quotations/display-board-futures"
_FUTOPT_FUTURES_BOARD_TR_ID = "FHPIF05030200"


# 국내옵션전광판_선물[국내선물-023]. market_cls_code=""(빈 값)이면 정규 KOSPI200선물
# (분기월 3·6·9·12월만 존재), "MKI"면 미니 KOSPI200선물(월물 전체 존재) - 46번 사전조사에서
# 실제 호출로 확인. 만기일 필드는 없다 - get_price()로 따로 조회해야 한다.
def get_futures_board(market_cls_code: str = "") -> list[dict]:
    settings = get_settings()
    response = httpx.get(
        f"{settings.kis_base_url}{_FUTOPT_FUTURES_BOARD_ENDPOINT}",
        headers={
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {get_access_token()}",
            "appkey": settings.kis_app_key,
            "appsecret": settings.kis_app_secret,
            "tr_id": _FUTOPT_FUTURES_BOARD_TR_ID,
            "custtype": "P",
        },
        params={
            "FID_COND_MRKT_DIV_CODE": "F",
            "FID_COND_SCR_DIV_CODE": "20503",
            "FID_COND_MRKT_CLS_CODE": market_cls_code,
        },
    )
    response.raise_for_status()
    body = response.json()
    return body.get("output") or []


_FUTOPT_CALLPUT_BOARD_ENDPOINT = "/uapi/domestic-futureoption/v1/quotations/display-board-callput"
_FUTOPT_CALLPUT_BOARD_TR_ID = "FHPIF05030100"


# 국내옵션전광판_콜풋[국내선물-022]. 특정 만기월(mtrt_yymm, 예: "202610")의 콜/풋 옵션
# 종목코드(optn_shrn_iscd)를 찾을 때 쓴다 - 옵션월물리스트만으로는 종목코드를 못 얻는다.
# 정규 선물이 없는 만기월(분기월이 아닌 달)의 만기일을 구하려면 이 종목코드로 get_price()를
# 호출해야 한다. output1에는 100건까지만 온다(KIS 공식 제약).
def get_option_callput_board(mtrt_yymm: str) -> list[dict]:
    settings = get_settings()
    response = httpx.get(
        f"{settings.kis_base_url}{_FUTOPT_CALLPUT_BOARD_ENDPOINT}",
        headers={
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {get_access_token()}",
            "appkey": settings.kis_app_key,
            "appsecret": settings.kis_app_secret,
            "tr_id": _FUTOPT_CALLPUT_BOARD_TR_ID,
            "custtype": "P",
        },
        params={
            "FID_COND_MRKT_DIV_CODE": "O",
            "FID_COND_SCR_DIV_CODE": "20503",
            "FID_MRKT_CLS_CODE": "CO",
            "FID_MTRT_CNT": mtrt_yymm,
            "FID_MRKT_CLS_CODE1": "PO",
            "FID_COND_MRKT_CLS_CODE": "",
        },
    )
    response.raise_for_status()
    body = response.json()
    return body.get("output1") or []


_FUTOPT_PRICE_ENDPOINT = "/uapi/domestic-futureoption/v1/quotations/inquire-price"
_FUTOPT_PRICE_TR_ID = "FHMIF10000000"


# 선물옵션 시세[v1_국내선물-006]. market_div_code: "F"=선물, "O"=옵션. iscd는 display-board-*
# 응답의 종목코드(futs_shrn_iscd/optn_shrn_iscd)를 그대로 넣는다.
# 응답의 futs_last_tr_date(YYYYMMDD)가 실제 최종거래일=만기일이다 - 46번 사전조사에서
# "해당 결제월의 두 번째 목요일"이라는 공식 규칙과 실제 값이 정확히 일치하는 것을 확인했다.
def get_price(market_div_code: str, iscd: str) -> dict:
    settings = get_settings()
    response = httpx.get(
        f"{settings.kis_base_url}{_FUTOPT_PRICE_ENDPOINT}",
        headers={
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {get_access_token()}",
            "appkey": settings.kis_app_key,
            "appsecret": settings.kis_app_secret,
            "tr_id": _FUTOPT_PRICE_TR_ID,
            "custtype": "P",
        },
        params={"FID_COND_MRKT_DIV_CODE": market_div_code, "FID_INPUT_ISCD": iscd},
    )
    response.raise_for_status()
    body = response.json()
    return body.get("output1") or {}