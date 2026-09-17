# kis_client.py
# 한국투자증권(KIS) API 직접 호출
# 토큰 발급 및 캐싱
# 국내/해외 지수, 환율 조회
#
# core에 있는 이유: 여러 도메인(timeline, heatmap 등)이 같이 쓸 수 있어야 하기 때문. 특히 토큰
# 발급/캐싱은 계좌 단위라서, 도메인마다 따로 만들면 재발급이 겹치거나 중복돼서 여기 하나로 모아둔다.

from __future__ import annotations

import json
import io
import threading
import time
import zipfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx

from backend.core.config import get_settings

# backend/src/backend/core/kis_client.py -> backend/ (프로젝트 최상위 폴더)
_TOKEN_CACHE_PATH = Path(__file__).resolve().parents[3] / ".cache" / "kis_token.json"
_TOKEN_ENDPOINT = "/oauth2/tokenP"
_INDEX_PRICE_ENDPOINT = "/uapi/domestic-stock/v1/quotations/inquire-index-price"
_INDEX_PRICE_TR_ID = "FHPUP02100000"
_OVERSEAS_INDEX_PRICE_ENDPOINT = "/uapi/overseas-price/v1/quotations/inquire-time-indexchartprice"
_OVERSEAS_INDEX_PRICE_TR_ID = "FHKST03030200"

_TOKEN_LOCK = threading.Lock()
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


# 캐시된 토큰 조회 (없거나 만료됐으면 None)
def _read_cached_token() -> str | None:
    if not _TOKEN_CACHE_PATH.exists():
        return None

    try:
        cached = json.loads(_TOKEN_CACHE_PATH.read_text(encoding="utf-8"))
        if cached["expires_at"] > time.time():
            return cached["access_token"]
    except (OSError, ValueError, KeyError, TypeError):
        # 중단된 쓰기나 이전 형식의 캐시는 재발급 경로로 복구한다.
        return None
    return None


# 새로 발급받은 토큰을 파일로 저장
def _write_cached_token(access_token: str, expires_in: int) -> None:
    _TOKEN_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = _TOKEN_CACHE_PATH.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(
            {
                "access_token": access_token,
                "expires_at": time.time() + expires_in - 60,  # 만료 60초 전까지는 캐시 재사용
            }
        ),
        encoding="utf-8",
    )
    temporary.replace(_TOKEN_CACHE_PATH)


# API 호출용 토큰 발급 (저장된 토큰 있으면 재사용, 없으면 새로 발급)
# 주의: 토큰을 너무 자주 새로 발급받으면 계좌 주인한테 알림이 가니, 이 함수 안 거치고 따로 발급하지 말 것
def get_access_token() -> str:
    # 최초 지표 수집/히트맵 수집이 동시에 시작되어도 발급은 한 번만 한다.
    with _TOKEN_LOCK:
        return _get_access_token_locked()


def _get_access_token_locked() -> str:
    cached_token = _read_cached_token()
    if cached_token:
        return cached_token

    settings = get_settings()
    response = _HTTP.post(
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
    return _get(
        _INDEX_PRICE_ENDPOINT,
        _INDEX_PRICE_TR_ID,
        {
            "FID_COND_MRKT_DIV_CODE": market_div_code,
            "FID_INPUT_ISCD": index_code,
        },
    )


# 해외 지수/환율 현재가 조회
# symbol로 대상 변경 가능 - S&P500="SPX", 나스닥="COMP", 니케이="JP#NI225", 달러환율="FX@KRW"
# market_div_code는 지수면 "N", 환율이면 "X"
def get_overseas_index_or_fx_price(market_div_code: str, symbol: str) -> dict:
    return _get(
        _OVERSEAS_INDEX_PRICE_ENDPOINT,
        _OVERSEAS_INDEX_PRICE_TR_ID,
        {
            "FID_COND_MRKT_DIV_CODE": market_div_code,
            "FID_INPUT_ISCD": symbol,
            "FID_HOUR_CLS_CODE": "0",
            "FID_PW_DATA_INCU_YN": "N",
        },
    )


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
    temporary.write_text(
        json.dumps(
            {"date": datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat(), "items": items},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
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
        sector_codes = [
            fields[offset : offset + 4]
            for offset in (3, 7, 11)
            if fields[offset : offset + 4].isdigit() and fields[offset : offset + 4] != "0000"
        ]

        def number(start: int, width: int) -> int:
            return int(fields[start : start + width].strip() or "0")

        items.append(
            {
                "code": code,
                "name": head[21:].strip(),
                "sector_code": sector_codes[-1] if sector_codes else "unclassified",
                "sector_codes": sector_codes,
                "market_cap": number(cap_offset, 9) * 100_000_000,
                "listed_shares": number(shares_offset, 15) * 1000,
                "reference_price": number(reference_offset, 9),
                "suspended": fields[suspended_offset] == "Y",
            }
        )
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

