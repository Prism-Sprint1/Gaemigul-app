# kis_client.py
# 한국투자증권(KIS) API 호출 (전 도메인 공용). 토큰 발급·캐싱, 재시도, 시세·순위·휴장일·투자자 매매동향·기간별 시세 조회.
# 토큰은 계좌 단위라 KIS 호출은 반드시 이 파일을 거친다 (토큰을 새로 발급할 때마다 계좌 주인에게 알림이 간다).

from __future__ import annotations

import json
import time
from pathlib import Path

import httpx

from backend.core.config import get_settings

# 토큰 캐시 파일 위치: backend/.cache/kis_token.json (git에 올리지 않는다)
_TOKEN_CACHE_PATH = Path(__file__).resolve().parents[3] / ".cache" / "kis_token.json"

# API 주소와 TR ID (KIS 문서 기준)
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
_INVESTOR_DAILY_ENDPOINT = "/uapi/domestic-stock/v1/quotations/inquire-investor-daily-by-market"
_INVESTOR_DAILY_TR_ID = "FHPTJ04040000"
_INDEX_DAILY_ENDPOINT = "/uapi/domestic-stock/v1/quotations/inquire-index-daily-price"
_INDEX_DAILY_TR_ID = "FHPUP02120000"
_OVERSEAS_PERIOD_ENDPOINT = "/uapi/overseas-price/v1/quotations/inquire-daily-chartprice"
_OVERSEAS_PERIOD_TR_ID = "FHKST03030100"

# 조회 실패 시 재시도 횟수, 대기(초, 시도마다 배수로 늘어남), 요청 타임아웃(초)
_RETRY_COUNT = 3
_RETRY_WAIT_SECONDS = 0.5
_TIMEOUT_SECONDS = 10.0


# 캐시된 토큰 (없거나 만료됐으면 None)
def _read_cached_token() -> str | None:
    if not _TOKEN_CACHE_PATH.exists():
        return None

    cached = json.loads(_TOKEN_CACHE_PATH.read_text())
    if cached["expires_at"] <= time.time():
        return None

    return cached["access_token"]


# 발급받은 토큰을 파일에 저장한다
def _write_cached_token(access_token: str, expires_in: int) -> None:
    _TOKEN_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _TOKEN_CACHE_PATH.write_text(
        json.dumps(
            {
                "access_token": access_token,
                "expires_at": time.time() + expires_in - 60,  # 만료 60초 전부터는 새로 발급
            }
        )
    )


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


# 조회 API 공통 GET
# 5xx(초당 한도 초과 EGW00201 포함)와 연결 오류는 _RETRY_COUNT번까지 재시도하고, 4xx는 바로 에러를 낸다
# 토큰 발급에는 쓰지 않는다 (재시도하면 알림이 여러 번 간다)
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

        if attempt < _RETRY_COUNT - 1:
            time.sleep(_RETRY_WAIT_SECONDS * (attempt + 1))

    raise last_error



# 접근 토큰. 캐시가 유효하면 재사용하고 없을 때만 새로 발급한다
# 토큰이 필요하면 반드시 이 함수를 쓴다 (따로 발급하면 계좌 주인에게 알림이 간다)
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


# 등락률 순위 (상위 30개) - 두 곳에서 쓴다
#   주도 섹터의 업종 내 상승 1위        sector_code=업종코드, market_div_code="J"
#   프리마켓·애프터마켓 급상승 종목     sector_code="0000", market_div_code="NX"
# sector_code: 업종코드면 그 업종 안에서, "0000"이면 시장 전체
# market_div_code: "J" 거래소(정규장 09:00~15:30) / "NX" 넥스트레이드(프리마켓 08:00~08:50, 애프터마켓 15:40~20:00) / "UN" 통합
# FID_RANK_SORT_CLS_CODE: "0" 상승률순 / "1" 하락률순
# 주의: "NX" 응답은 등락률순이 아니다. 받는 쪽에서 prdy_ctrt로 다시 정렬할 것
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
            "FID_RANK_SORT_CLS_CODE": "0",
            "FID_INPUT_CNT_1": "0",
            "FID_PRC_CLS_CODE": "0",
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


# 업종 지수 시간별 체결 (지금부터 거슬러 최근 100틱) - 지금은 호출하는 곳 없음
# index_code: "0001"(코스피) / 업종코드, interval_seconds: 틱 간격 "60" / "30"
# 주의: 과거 시각은 조회할 수 없다. 체결이 없는 자리에 "99:99:99" 같은 더미 행이 오니 시(hour)가 00~23인 행만 쓸 것
# 응답 output: bsop_hour(HHMMSS) / bstp_nmix_prpr(지수) / bstp_nmix_prdy_ctrt(등락률)
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
