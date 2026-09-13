# report_data_service.py
# 일간·주간 보고서의 수치(카드·차트에 들어가는 숫자)를 KIS에서 모은다. LLM 문구·이미지는 report_service가 만든다.
#   collect_daily_data            일간 수치 수집 (동기 - KIS 호출이 동기라서. async 코드에서는 asyncio.to_thread로 부른다)
#   collect_and_save_daily        그날 15:30 슬롯의 주도 섹터를 읽어 일간 수치를 수집하고 report_repository에 저장
#   collect_weekly_data           주간 수치 수집 (투자자 순매수는 일간 보고서 합, VKOSPI·분기 차트는 API) (동기)
#   collect_weekly_sector_cards   주간 섹터 카드 후보 조회 (동기)
#
# 항목마다 따로 실패를 처리한다. 한 항목이 실패하면 경고 로그만 남기고 그 키를 결과에서 뺀다
#   (report_repository.save_report_data는 없는 키의 기존 값을 유지한다)
# 금액 단위는 전부 백만원 (KIS 응답 그대로)

import asyncio
import logging
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core import kis_client
from backend.domain.timeline.models.report import TimelineReport
from backend.domain.timeline.services import leading_sector_service, report_repository, timeline_repository

_KST = ZoneInfo("Asia/Seoul")

logger = logging.getLogger(__name__)

# VKOSPI 업종코드
_VKOSPI_CODE = "0503"

# 원달러 환율 심볼 (해외 기간별 시세)
_FX_SYMBOL = "FX@KRW"

# 차트에 넣는 분기 수 (현 분기 포함). 바꾸면 차트 막대 수가 바뀐다
_QUARTER_COUNT = 6

# 투자자 매매동향을 과거로 거슬러 받을 최대 호출 수 (1회 300거래일 = 약 14개월). 분기 6개면 2회로 충분하다
_INVESTOR_MAX_CALLS = 3

# 섹터 카드 재료로 읽는 슬롯 (장 마감 주도 섹터)
_SECTOR_SOURCE_SLOT = "15:30"

# 업종명 -> 업종코드 (leading_sector_service.KOSPI_SECTOR_CODES를 뒤집는다. 업종 표는 그쪽에서 고친다)
_SECTOR_NAME_TO_CODE = {name: code for code, name in leading_sector_service.KOSPI_SECTOR_CODES.items()}


# "20260911" 형태로
def _ymd(day: date) -> str:
    return day.strftime("%Y%m%d")


# "20260911" -> date
def _parse_ymd(value: str) -> date:
    return datetime.strptime(value, "%Y%m%d").date()


# 분기 (연도, 1~4)
def _quarter_of(day: date) -> tuple[int, int]:
    return day.year, (day.month - 1) // 3 + 1


# 보고서 날짜의 분기 + 직전 분기들 (오래된 분기부터 _QUARTER_COUNT개). 날짜로 계산하므로 분기가 바뀌면 자동으로 밀린다
def _quarter_window(day: date) -> list[tuple[int, int]]:
    year, quarter = _quarter_of(day)
    index = year * 4 + (quarter - 1)
    return [(i // 4, i % 4 + 1) for i in range(index - _QUARTER_COUNT + 1, index + 1)]


# 분기 첫날
def _quarter_start(year: int, quarter: int) -> date:
    return date(year, 3 * (quarter - 1) + 1, 1)


# 차트 라벨 (예: "26/Q3")
def _quarter_label(year: int, quarter: int) -> str:
    return f"{year % 100:02d}/Q{quarter}"


# 투자자 매매동향 행을 earliest 날짜까지 거슬러 모은다 (최신부터, 날짜 중복 없음)
# 한 번에 300거래일이 오므로 가장 오래된 행의 전날로 기준일을 옮겨 다시 부른다
def _investor_rows(day: date, earliest: date) -> list[dict]:
    rows: list[dict] = []
    base = day
    for _ in range(_INVESTOR_MAX_CALLS):
        output = kis_client.get_investor_daily_by_market(_ymd(base)).get("output") or []
        new_rows = [row for row in output if row.get("stck_bsop_date") and _parse_ymd(row["stck_bsop_date"]) <= base]
        if not new_rows:
            break
        rows.extend(new_rows)
        oldest = min(_parse_ymd(row["stck_bsop_date"]) for row in new_rows)
        if oldest <= earliest:
            break
        base = oldest - timedelta(days=1)
    return rows


# 그날 코스피 투자자별 순매수 {"foreign_net_buy", "institution_net_buy", "individual_net_buy"}. 그날 행이 없으면 None
def _daily_investor(rows: list[dict], day: date) -> dict | None:
    for row in rows:
        if row.get("stck_bsop_date") == _ymd(day):
            return {
                "foreign_net_buy": int(row["frgn_ntby_tr_pbmn"]),
                "institution_net_buy": int(row["orgn_ntby_tr_pbmn"]),
                "individual_net_buy": int(row["prsn_ntby_tr_pbmn"]),
            }
    return None


# 그날 VKOSPI 종가·전일 대비 등락률 {"vkospi", "vkospi_change_rate"}. 그날 행이 없으면 None
def _daily_vkospi(day: date) -> dict | None:
    output2 = kis_client.get_index_daily_price(_VKOSPI_CODE, _ymd(day), "D").get("output2") or []
    for row in output2:
        if row.get("stck_bsop_date") == _ymd(day):
            return {"vkospi": float(row["bstp_nmix_prpr"]), "vkospi_change_rate": float(row["bstp_nmix_prdy_ctrt"])}
    return None


# 분기 차트 6행 [{"label", "usd_krw", "foreign_net_buy", "is_current"}] (오래된 분기부터)
#   외국인: 분기 안 거래일 순매수 합 (현 분기는 보고서 날짜까지). 그 분기 행이 하나도 없으면 None
#   환율: 분기 안 가장 늦은 달의 월간 종가 (지난 분기는 분기 마지막 달, 현 분기는 이번 달 최신 값). 0 값은 버린다
def _quarters(day: date, investor_rows: list[dict]) -> list[dict]:
    window = _quarter_window(day)
    start = _quarter_start(*window[0])

    fx_rows = kis_client.get_overseas_period_price("X", _FX_SYMBOL, _ymd(start), _ymd(day), "M").get("output2") or []
    fx_by_quarter: dict[tuple[int, int], tuple[date, float]] = {}
    for row in fx_rows:
        price = float(row.get("ovrs_nmix_prpr") or 0)
        if not row.get("stck_bsop_date") or price <= 0:
            continue
        month = _parse_ymd(row["stck_bsop_date"])
        key = _quarter_of(month)
        if key not in fx_by_quarter or month > fx_by_quarter[key][0]:
            fx_by_quarter[key] = (month, price)

    foreign_by_quarter: dict[tuple[int, int], int] = {}
    seen_dates: set[str] = set()
    for row in investor_rows:
        ymd = row.get("stck_bsop_date")
        if not ymd or ymd in seen_dates:
            continue
        seen_dates.add(ymd)
        row_date = _parse_ymd(ymd)
        if row_date < start or row_date > day:
            continue
        key = _quarter_of(row_date)
        foreign_by_quarter[key] = foreign_by_quarter.get(key, 0) + int(row["frgn_ntby_tr_pbmn"])

    current = window[-1]
    return [
        {
            "label": _quarter_label(*key),
            "usd_krw": fx_by_quarter[key][1] if key in fx_by_quarter else None,
            "foreign_net_buy": foreign_by_quarter.get(key),
            "is_current": key == current,
        }
        for key in window
    ]


# 섹터 카드 1개 {"sector_name", "change_rate", "rising_count", "total_count", "trade_amount", "prev_trade_amount"}
#   등락률·거래대금은 output2의 그날 행, 전일 거래대금은 그 바로 전 행에서 가져온다 (날짜 지정이 되므로 나중에도 정확)
#   상승·전체 종목 수는 output1에만 있고 output1은 항상 최근 거래일 값이다
#     -> output1 거래대금이 그날 행과 같을 때(= 최근 거래일이 그날)만 채우고, 아니면 None
#   업종명이 업종 표에 없으면 경고를 남기고 이름만 있는 카드를 돌려준다
def _sector_card(name: str, day: date) -> dict:
    card = {"sector_name": name, "change_rate": None, "rising_count": None, "total_count": None, "trade_amount": None, "prev_trade_amount": None}

    code = _SECTOR_NAME_TO_CODE.get(name)
    if code is None:
        logger.warning("섹터 카드 - 업종 표에 없는 업종명이라 값을 비웁니다: %s", name)
        return card

    body = kis_client.get_index_daily_price(code, _ymd(day), "D")
    output1 = body.get("output1") or {}
    output2 = body.get("output2") or []

    index = next((i for i, row in enumerate(output2) if row.get("stck_bsop_date") == _ymd(day)), None)
    if index is None:
        logger.warning("섹터 카드 - %s %s 일자 행이 없습니다.", name, day)
        return card

    today_row = output2[index]
    card["change_rate"] = float(today_row["bstp_nmix_prdy_ctrt"])
    card["trade_amount"] = int(today_row["acml_tr_pbmn"])
    if index + 1 < len(output2):
        card["prev_trade_amount"] = int(output2[index + 1]["acml_tr_pbmn"])

    if output1.get("acml_tr_pbmn") == today_row.get("acml_tr_pbmn"):
        rising = int(output1["ascn_issu_cnt"])
        card["rising_count"] = rising
        card["total_count"] = rising + int(output1["down_issu_cnt"]) + int(output1["stnr_issu_cnt"])
    else:
        logger.warning("섹터 카드 - %s: 최근 거래일이 %s이 아니라 상승 종목 수를 비웁니다 (다음 개장 전까지만 받을 수 있다).", name, day)

    return card


# 일간 보고서 수치 수집 -> report_repository.save_report_data의 data 형식
#   day           보고서 날짜 (거래일)
#   sector_names  섹터 카드로 쓸 업종명 (그날 15:30 주도 섹터, 카드 순서대로)
# 실패한 항목은 키를 빼고 돌려준다
def collect_daily_data(day: date, sector_names: list[str]) -> dict:
    data: dict = {}
    window_start = _quarter_start(*_quarter_window(day)[0])

    investor_rows: list[dict] = []
    try:
        investor_rows = _investor_rows(day, window_start)
        investor = _daily_investor(investor_rows, day)
        if investor is None:
            logger.warning("일간 보고서 %s - 투자자 매매동향에 그날 행이 없습니다.", day)
        else:
            data.update(investor)
    except Exception as error:
        logger.warning("일간 보고서 %s - 투자자 매매동향 조회 실패 - %s: %s", day, type(error).__name__, error)

    try:
        vkospi = _daily_vkospi(day)
        if vkospi is None:
            logger.warning("일간 보고서 %s - VKOSPI 그날 행이 없습니다.", day)
        else:
            data.update(vkospi)
    except Exception as error:
        logger.warning("일간 보고서 %s - VKOSPI 조회 실패 - %s: %s", day, type(error).__name__, error)

    # 투자자 행이 없으면 분기 외국인 합이 전부 비므로 차트를 저장하지 않는다 (기존 차트 유지)
    if investor_rows:
        try:
            data["quarters"] = _quarters(day, investor_rows)
        except Exception as error:
            logger.warning("일간 보고서 %s - 분기 차트 계산 실패 - %s: %s", day, type(error).__name__, error)

    if sector_names:
        cards = []
        for name in sector_names:
            try:
                cards.append(_sector_card(name, day))
            except Exception as error:
                logger.warning("일간 보고서 %s - 섹터 카드 %s 조회 실패 - %s: %s", day, name, type(error).__name__, error)
                cards.append({"sector_name": name})
        data["sectors"] = cards
    else:
        logger.warning("일간 보고서 %s - 15:30 주도 섹터가 없어 섹터 카드를 만들지 않습니다.", day)

    return data


# 그날 15:30 슬롯의 주도 섹터를 읽어 수치를 모으고 저장한다. 저장된 보고서를 돌려준다
#   day를 비우면 오늘(한국 시간)
# 섹터 카드 순서는 15:30 등락률 높은 순이다
async def collect_and_save_daily(session: AsyncSession, day: date | None = None) -> TimelineReport:
    day = day or datetime.now(_KST).date()

    slot = await timeline_repository.load_slot(session, day, _SECTOR_SOURCE_SLOT)
    sectors = sorted(slot.leading_sectors, key=lambda sector: sector.change_rate, reverse=True) if slot else []
    sector_names = [sector.name for sector in sectors]

    data = await asyncio.to_thread(collect_daily_data, day, sector_names)
    return await report_repository.save_report_data(session, report_repository.DAILY, day, day, data)


# 주간 VKOSPI 종가·전주 대비 등락률. 주별 행의 날짜는 그 주 월요일이다. 그 주 행이 없으면 None
def _weekly_vkospi(start_date: date, end_date: date) -> dict | None:
    monday = start_date - timedelta(days=start_date.weekday())
    output2 = kis_client.get_index_daily_price(_VKOSPI_CODE, _ymd(end_date), "W").get("output2") or []
    for row in output2:
        if row.get("stck_bsop_date") and monday <= _parse_ymd(row["stck_bsop_date"]) <= end_date:
            return {"vkospi": float(row["bstp_nmix_prpr"]), "vkospi_change_rate": float(row["bstp_nmix_prdy_ctrt"])}
    return None


# 주간 섹터 카드 1개. 주별 output2의 그 주 행(등락률·거래대금)과 바로 전 행(전주 거래대금)
# 상승·전체 종목 수는 주간 값이 없어 None으로 둔다 (기준 미정 - Claude.md '미정' 참고)
def _weekly_sector_card(name: str, start_date: date, end_date: date) -> dict:
    card = {"sector_name": name, "change_rate": None, "rising_count": None, "total_count": None, "trade_amount": None, "prev_trade_amount": None}

    code = _SECTOR_NAME_TO_CODE.get(name)
    if code is None:
        logger.warning("주간 섹터 카드 - 업종 표에 없는 업종명이라 값을 비웁니다: %s", name)
        return card

    monday = start_date - timedelta(days=start_date.weekday())
    output2 = kis_client.get_index_daily_price(code, _ymd(end_date), "W").get("output2") or []
    index = next((i for i, row in enumerate(output2) if row.get("stck_bsop_date") and monday <= _parse_ymd(row["stck_bsop_date"]) <= end_date), None)
    if index is None:
        logger.warning("주간 섹터 카드 - %s %s 주 행이 없습니다.", name, start_date)
        return card

    card["change_rate"] = float(output2[index]["bstp_nmix_prdy_ctrt"])
    card["trade_amount"] = int(output2[index]["acml_tr_pbmn"])
    if index + 1 < len(output2):
        card["prev_trade_amount"] = int(output2[index + 1]["acml_tr_pbmn"])
    return card


# 주간 보고서 수치 수집 -> save_report_data의 data 형식 (sectors 제외)
#   daily_reports  그 주 일간 보고서 (report_repository.load_daily_reports)
# 투자자 순매수는 일간 보고서 값의 합이다. 값이 빈 일간 보고서가 있으면 경고를 남기고 있는 날만 더한다
# 차트 분기는 주 마지막 거래일 기준으로 다시 계산한다 (지난 분기 값은 배경 데이터라 API로 조회)
def collect_weekly_data(start_date: date, end_date: date, daily_reports: list[TimelineReport]) -> dict:
    data: dict = {}

    for field in ("foreign_net_buy", "institution_net_buy", "individual_net_buy"):
        values = [getattr(report, field) for report in daily_reports if getattr(report, field) is not None]
        if len(values) < len(daily_reports):
            logger.warning("주간 보고서 %s - %s 값이 빈 일간 보고서가 있어 %d/%d일만 더합니다.", start_date, field, len(values), len(daily_reports))
        if values:
            data[field] = sum(values)

    try:
        vkospi = _weekly_vkospi(start_date, end_date)
        if vkospi is None:
            logger.warning("주간 보고서 %s - VKOSPI 주간 행이 없습니다.", start_date)
        else:
            data.update(vkospi)
    except Exception as error:
        logger.warning("주간 보고서 %s - VKOSPI 조회 실패 - %s: %s", start_date, type(error).__name__, error)

    try:
        investor_rows = _investor_rows(end_date, _quarter_start(*_quarter_window(end_date)[0]))
        if investor_rows:
            data["quarters"] = _quarters(end_date, investor_rows)
    except Exception as error:
        logger.warning("주간 보고서 %s - 분기 차트 계산 실패 - %s: %s", start_date, type(error).__name__, error)

    return data


# 주간 섹터 카드 후보 전체를 조회한다 (LLM이 이 중에서 고른다). 실패한 업종은 이름만 있는 카드
def collect_weekly_sector_cards(names: list[str], start_date: date, end_date: date) -> list[dict]:
    cards = []
    for name in names:
        try:
            cards.append(_weekly_sector_card(name, start_date, end_date))
        except Exception as error:
            logger.warning("주간 섹터 카드 %s 조회 실패 - %s: %s", name, type(error).__name__, error)
            cards.append({"sector_name": name})
    return cards
