# report_service.py
# 일간·주간 보고서를 만든다. 수치 수집(report_data_service) -> LLM 문구 -> 섹터 카드 선택 -> 이미지 -> 저장(report_repository).
#   generate_daily           일간 보고서 생성·저장 (20:00 슬롯 직후, POST /timeline/report/daily)
#   generate_weekly          주간 보고서 생성·저장 (그 주 마지막 거래일 일간 보고서 직후, POST /timeline/report/weekly)
#   get_report               날짜로 보고서 조회 (GET /timeline/report)
#   to_response              DB 보고서 -> 응답 DTO (비율·증감률 계산 포함)
#   run_scheduled_reports    20:00 슬롯이 끝나면 timeline_service가 부른다 (휴장일·마지막 거래일 판단 + 실패 로깅)
#
# LLM 문구는 타임라인 브리핑과 같은 원칙으로 만든다
#   먼저 수치를 저장하고, 그 수치를 [확정 수치]로, 타임라인 글·뉴스를 따로 나눠 넘겨 없는 숫자를 만들지 못하게 한다
#   카드·차트 숫자는 LLM이 쓰지 않고 코드가 채운다
# 단계마다 따로 저장하므로 LLM이나 이미지가 실패해도 앞 단계 값은 남는다

import asyncio
import json
import logging
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core import image_client, llm_client, storage_client
from backend.core.database import get_session_factory
from backend.domain.timeline.models.report import TimelineReport, TimelineReportSector
from backend.domain.timeline.models.timeline import TimelineSlot
from backend.domain.timeline.schemas.report import ReportKeywordItem, ReportQuarterItem, ReportResponse, ReportSectionItem, ReportSectorItem, ReportTermItem
from backend.domain.timeline.services import glossary, market_hours, prompts, report_data_service, report_repository, timeline_repository

_KST = ZoneInfo("Asia/Seoul")

logger = logging.getLogger(__name__)

# 섹션·핵심 요약·키워드·용어·섹터 카드 개수. 바꾸면 저장 개수가 바뀐다 (프롬프트 [길이]·[출력 형식]도 같이 맞출 것)
_SECTION_COUNT = 3
_POINT_COUNT = 3
_KEYWORD_COUNT = 3
_TERM_COUNT = 3
_SECTOR_CARD_COUNT = 3

# 이미지를 올릴 Supabase Storage 공개 버킷
_IMAGE_BUCKET = "report-images"

# DB 칼럼 길이 (models/report.py와 같게). LLM이 길이 제한을 어겨도 저장이 실패하지 않게 자른다
_MAX_TITLE = 200
_MAX_SUMMARY = 300
_MAX_SHORT = 100


# 백만원 -> "-2조 2,984억원" 같은 읽기 쉬운 문자열 (LLM 입력용. LLM이 단위를 잘못 옮기지 않게 코드가 바꾼다)
def _won(million: int | None) -> str | None:
    if million is None:
        return None
    sign = "-" if million < 0 else "+"
    eok = round(abs(million) / 100)
    jo, rest = divmod(eok, 10000)
    if jo and rest:
        return f"{sign}{jo}조 {rest:,}억원"
    if jo:
        return f"{sign}{jo}조원"
    return f"{sign}{rest:,}억원"


# 비율 문자열 "+30%" (전일·전주 대비 거래대금 증감). 비교값이 없으면 None
def _change_percent(current: int | None, previous: int | None) -> str | None:
    if not current or not previous:
        return None
    return f"{(current - previous) / previous * 100:+.0f}%"


# 섹터 카드 dict -> LLM 입력용 확정 수치
def _sector_fact(card: dict) -> dict:
    fact = {"업종": card["sector_name"], "등락률(%)": card.get("change_rate"), "거래대금": _won(card.get("trade_amount")), "거래대금 증감": _change_percent(card.get("trade_amount"), card.get("prev_trade_amount"))}
    if card.get("rising_count") is not None and card.get("total_count"):
        fact["상승 종목"] = f"{card['total_count']}개 중 {card['rising_count']}개"
    return {key: value for key, value in fact.items() if value is not None}


# 보고서 수치 -> LLM 입력용 확정 수치 (투자자 순매수·VKOSPI·분기 차트)
def _report_facts(report: TimelineReport) -> dict:
    facts = {
        "코스피 외국인 순매수": _won(report.foreign_net_buy),
        "코스피 기관 순매수": _won(report.institution_net_buy),
        "코스피 개인 순매수": _won(report.individual_net_buy),
        "VKOSPI": report.vkospi,
        "VKOSPI 등락률(%)": report.vkospi_change_rate,
        "분기별 원달러 환율·외국인 순매수": [
            {"분기": quarter.label + (" (진행 중)" if quarter.is_current else ""), "환율": quarter.usd_krw, "외국인 순매수": _won(quarter.foreign_net_buy)}
            for quarter in report.quarters
        ],
    }
    return {key: value for key, value in facts.items() if value not in (None, [])}


# ORM 섹터 행 -> 카드 dict (save_report_data 형식)
def _card_from_row(row: TimelineReportSector) -> dict:
    return {
        "sector_name": row.sector_name,
        "change_rate": row.change_rate,
        "rising_count": row.rising_count,
        "total_count": row.total_count,
        "trade_amount": row.trade_amount,
        "prev_trade_amount": row.prev_trade_amount,
    }


# 일간 보고서 재료 JSON. 확정 수치(보고서 수치 + 타임라인 시세) / 타임라인(슬롯 브리핑) / 뉴스(슬롯 뉴스, 링크 중복 제거)
def _daily_input(report: TimelineReport, slots: list[TimelineSlot], cards: list[dict]) -> str:
    facts = _report_facts(report)
    facts["섹터 후보"] = [_sector_fact(card) for card in cards]

    slot_facts = []
    timeline = []
    news = []
    seen_urls: set[str] = set()
    for slot in slots:
        values = {
            "지표": [{"이름": row.name, "가격": row.price, "등락률(%)": row.change_rate} for row in slot.indicators],
            "장중 변화": [{"이름": row.name, "07:30 가격": row.morning_price, "마감 가격": row.closing_price, "변동률(%)": row.change_rate} for row in slot.intraday_changes],
            "주도 섹터": [
                {"업종": sector.name, "등락률(%)": sector.change_rate, "종목": [{"이름": stock.name, "등락률(%)": stock.change_rate, "구분": stock.label} for stock in sector.stocks]}
                for sector in slot.leading_sectors
            ],
            "급상승 종목": [{"이름": row.name, "등락률(%)": row.change_rate, "가격": row.price} for row in slot.top_gainers],
        }
        values = {key: value for key, value in values.items() if value}
        if values:
            slot_facts.append({"시각": slot.time_slot, **values})

        if slot.briefing_headline:
            timeline.append({"시각": slot.time_slot, "제목": slot.briefing_headline, "부제": slot.briefing_subtitle, "포인트": [f"{row.title}: {row.body}" for row in slot.insights]})

        for row in slot.news:
            if row.url in seen_urls:
                continue
            seen_urls.add(row.url)
            news.append({"발행시각": f"{row.published_at:%m-%d %H:%M}" if row.published_at else None, "제목": row.title, "요약": row.summary})

    facts["시간대별 시세"] = slot_facts
    payload = {"확정 수치": {key: value for key, value in facts.items() if value}, "타임라인": timeline, "뉴스": news}
    return json.dumps(payload, ensure_ascii=False, indent=2)


# 주간 보고서 재료 JSON. 확정 수치(주간 수치 + 일별 외국인 순매수 + 섹터 후보 주간 값) / 일간 보고서(문구)
def _weekly_input(report: TimelineReport, daily_reports: list[TimelineReport], cards: list[dict]) -> str:
    facts = _report_facts(report)
    # 주간 합계임을 LLM이 알도록 이름을 바꾼다
    for key in ("코스피 외국인 순매수", "코스피 기관 순매수", "코스피 개인 순매수"):
        if key in facts:
            facts[f"{key} (주간 합계)"] = facts.pop(key)
    if "VKOSPI 등락률(%)" in facts:
        facts["VKOSPI 전주 대비 등락률(%)"] = facts.pop("VKOSPI 등락률(%)")
    facts["일별 외국인 순매수"] = [{"날짜": f"{daily.start_date:%m-%d}", "외국인 순매수": _won(daily.foreign_net_buy)} for daily in daily_reports if daily.foreign_net_buy is not None]
    facts["섹터 후보 (주간 등락률·주간 거래대금·전주 대비)"] = [_sector_fact(card) for card in cards]

    dailies = [
        {
            "날짜": f"{daily.start_date:%m-%d}",
            "제목": daily.title,
            "한 줄 요약": daily.summary,
            "섹션": [{"제목": section.title, "설명": section.description, "핵심 요약": [point.body for point in section.points]} for section in daily.sections],
            "결론": daily.conclusion,
        }
        for daily in daily_reports
        if daily.title
    ]
    payload = {"확정 수치": {key: value for key, value in facts.items() if value}, "일간 보고서": dailies}
    return json.dumps(payload, ensure_ascii=False, indent=2)


# 문자열 값을 꺼내 다듬는다 (없거나 문자열이 아니면 빈 문자열)
def _text(value, limit: int | None = None) -> str:
    text = value.strip() if isinstance(value, str) else ""
    return text[:limit] if limit else text


# LLM 응답 -> save_report_content 형식 (용어 제외). 필수 값이 빠졌으면 None
def _parse_content(answer: dict) -> dict | None:
    sections = []
    for section in (answer.get("sections") or [])[:_SECTION_COUNT]:
        if not isinstance(section, dict):
            continue
        points = [_text(point) for point in (section.get("points") or []) if _text(point)][:_POINT_COUNT]
        if _text(section.get("title")) and _text(section.get("description")) and points:
            sections.append({"title": _text(section["title"], _MAX_TITLE), "description": _text(section["description"]), "points": points})

    keywords = [
        {"title": _text(item.get("title"), _MAX_SHORT), "description": _text(item.get("description"))}
        for item in (answer.get("keywords") or [])
        if isinstance(item, dict) and _text(item.get("title")) and _text(item.get("description"))
    ][:_KEYWORD_COUNT]

    title, summary, conclusion = _text(answer.get("title"), _MAX_TITLE), _text(answer.get("summary"), _MAX_SUMMARY), _text(answer.get("conclusion"), _MAX_SUMMARY)
    if not (title and summary and conclusion) or len(sections) < _SECTION_COUNT:
        return None

    return {"title": title, "summary": summary, "conclusion": conclusion, "sections": sections, "keywords": keywords}


# 어려운 용어 3개 고르기
#   1. glossary 사전 용어 중 본문에 나온 것 - 결론·핵심 요약·키워드에 나온 것 먼저, 그다음 본문에 먼저 나온 순서 (설명은 사전 값, source "GLOSSARY")
#   2. 모자라면 LLM이 고른 용어 중 본문에 실제로 있는 것 (설명은 LLM 값, source "LLM" - 검토 후 사전 등록 후보)
def _pick_terms(content: dict, llm_terms: list) -> list[dict]:
    priority_text = " ".join([content["conclusion"]] + [point for section in content["sections"] for point in section["points"]] + [f"{item['title']} {item['description']}" for item in content["keywords"]])
    body_text = " ".join([content["title"], content["summary"], priority_text] + [f"{section['title']} {section['description']}" for section in content["sections"]])

    hits = [term for term in glossary.GLOSSARY if term in body_text]
    hits.sort(key=lambda term: (term not in priority_text, body_text.find(term)))
    picked = [{"term": term, "description": glossary.GLOSSARY[term], "source": "GLOSSARY"} for term in hits[:_TERM_COUNT]]

    for item in llm_terms:
        if len(picked) >= _TERM_COUNT:
            break
        if not isinstance(item, dict):
            continue
        term, description = _text(item.get("term"), _MAX_SHORT), _text(item.get("description"))
        if not term or not description or term not in body_text or any(row["term"] == term for row in picked):
            continue
        if term in glossary.GLOSSARY:
            picked.append({"term": term, "description": glossary.GLOSSARY[term], "source": "GLOSSARY"})
        else:
            picked.append({"term": term, "description": description, "source": "LLM"})

    return picked


# 섹터 카드 고르기. LLM이 고른 후보 업종명 순서대로, 모자라면 남은 후보를 원래 순서대로 채워 최대 3개
def _pick_sector_cards(llm_sectors: list, cards: list[dict]) -> list[dict]:
    by_name = {card["sector_name"]: card for card in cards}
    names = []
    for name in llm_sectors or []:
        if isinstance(name, str) and name.strip() in by_name and name.strip() not in names:
            names.append(name.strip())
    for card in cards:
        if card["sector_name"] not in names:
            names.append(card["sector_name"])
    return [by_name[name] for name in names[:_SECTOR_CARD_COUNT]]


# LLM으로 보고서 문구를 만든다 (동기). 실패하면 None
# 반환: {"content": save_report_content 형식, "sectors": LLM이 고른 업종명, "main_scene", "section1_scene"}
def _generate_content(report_type: str, start_date: date, end_date: date, data: str, candidates: list[str]) -> dict | None:
    try:
        answer = llm_client.generate_json(
            prompts.REPORT_PROMPT.format(
                period=prompts.REPORT_PERIOD[report_type],
                start_date=start_date,
                end_date=end_date,
                sector_candidates=", ".join(candidates) if candidates else "(없음)",
                data=data,
            ),
            timeout=120.0,
        )
    except (RuntimeError, ValueError, KeyError, httpx.HTTPError) as error:
        logger.warning("%s %s 보고서 문구 생성 실패 - %s: %s", report_type, start_date, type(error).__name__, error)
        return None

    content = _parse_content(answer)
    if content is None:
        logger.warning("%s %s 보고서 응답에 필요한 값이 없습니다.", report_type, start_date)
        return None

    content["terms"] = _pick_terms(content, answer.get("terms") or [])
    return {
        "content": content,
        "sectors": answer.get("sectors") or [],
        "main_scene": _text(answer.get("main_image_scene")),
        "section1_scene": _text(answer.get("section1_image_scene")),
    }


# 장면 묘사로 이미지를 만들어 올리고 공개 URL을 돌려준다 (동기). 실패하면 None
# 경로에 생성 시각을 넣는다 - 같은 경로에 덮어쓰면 CDN 캐시 때문에 한동안 옛 이미지가 보인다
def _make_image(scene: str, report_type: str, start_date: date, name: str) -> str | None:
    if not scene:
        logger.warning("%s %s %s 이미지 장면 묘사가 없어 건너뜁니다.", report_type, start_date, name)
        return None
    try:
        image = image_client.generate_image(f"{scene}, {prompts.IMAGE_STYLE}")
        path = f"{report_type.lower()}/{start_date}/{name}_{datetime.now(_KST):%H%M%S}.jpg"
        return storage_client.upload_file(_IMAGE_BUCKET, path, image, "image/jpeg")
    except (RuntimeError, KeyError, ValueError, httpx.HTTPError) as error:
        logger.warning("%s %s %s 이미지 생성·업로드 실패 - %s: %s", report_type, start_date, name, type(error).__name__, error)
        return None


# 문구 -> 섹터 카드 -> 문구 저장 -> 이미지 저장 (일간·주간 공통 뒷부분)
#   report  수치까지 저장된 보고서
# 문구 생성이 실패하면 기존 문구·섹터 카드를 그대로 두고 돌려준다
#   섹터 카드가 아직 없을 때만(주간 첫 생성) 후보 앞 3개를 저장한다
async def _write_report(session: AsyncSession, report: TimelineReport, data: str, cards: list[dict]) -> TimelineReport:
    report_type, start_date, end_date = report.report_type, report.start_date, report.end_date
    candidates = [card["sector_name"] for card in cards]
    generated = await asyncio.to_thread(_generate_content, report_type, start_date, end_date, data, candidates)
    if generated is None:
        if report.sectors or not cards:
            return report
        return await report_repository.save_report_data(session, report_type, start_date, end_date, {"sectors": cards[:_SECTOR_CARD_COUNT]})

    await report_repository.save_report_data(session, report_type, start_date, end_date, {"sectors": _pick_sector_cards(generated["sectors"], cards)})
    await report_repository.save_report_content(session, report_type, start_date, generated["content"])

    main_url, section1_url = await asyncio.gather(
        asyncio.to_thread(_make_image, generated["main_scene"], report_type, start_date, "main"),
        asyncio.to_thread(_make_image, generated["section1_scene"], report_type, start_date, "section1"),
    )
    return await report_repository.save_report_images(session, report_type, start_date, main_image_url=main_url, section1_image_url=section1_url)


# 일간 보고서를 만들어 저장한다. day를 비우면 오늘(한국 시간)
# 순서: 수치 수집·저장 -> 그날 타임라인 슬롯 읽기 -> 문구 -> 섹터 카드 순서 -> 이미지
async def generate_daily(session: AsyncSession, day: date | None = None) -> TimelineReport:
    day = day or datetime.now(_KST).date()

    report = await report_data_service.collect_and_save_daily(session, day)
    cards = [_card_from_row(row) for row in report.sectors]
    slots = await timeline_repository.load_day(session, day)
    if not slots:
        logger.warning("일간 보고서 %s - 그날 타임라인 슬롯이 없습니다. 수치만으로 문구를 만듭니다.", day)

    return await _write_report(session, report, _daily_input(report, slots, cards), cards)


# day가 속한 주(월~금)의 거래일 목록
def _week_trading_days(day: date) -> list[date]:
    monday = day - timedelta(days=day.weekday())
    return [monday + timedelta(days=offset) for offset in range(5) if market_hours.is_trading_day(monday + timedelta(days=offset))]


# 주간 보고서를 만들어 저장한다. day가 속한 주가 대상이다 (비우면 오늘)
# 재료는 그 주 일간 보고서다. 일간 보고서가 하나도 없으면 만들지 않고 None
# 섹터 후보는 그 주 일간 보고서에 저장된 섹터 카드의 업종명 전체 (중복 제거, 먼저 나온 순서)
async def generate_weekly(session: AsyncSession, day: date | None = None) -> TimelineReport | None:
    day = day or datetime.now(_KST).date()
    trading_days = await asyncio.to_thread(_week_trading_days, day)
    if not trading_days:
        logger.warning("주간 보고서 %s - 그 주에 거래일이 없습니다.", day)
        return None
    start_date, end_date = trading_days[0], trading_days[-1]

    daily_reports = await report_repository.load_daily_reports(session, start_date, end_date)
    if not daily_reports:
        logger.warning("주간 보고서 %s~%s - 일간 보고서가 없어 만들지 않습니다.", start_date, end_date)
        return None

    names = list(dict.fromkeys(row.sector_name for daily in daily_reports for row in daily.sectors))
    data = await asyncio.to_thread(report_data_service.collect_weekly_data, start_date, end_date, daily_reports)
    cards = await asyncio.to_thread(report_data_service.collect_weekly_sector_cards, names, start_date, end_date)

    report = await report_repository.save_report_data(session, report_repository.WEEKLY, start_date, end_date, data)
    return await _write_report(session, report, _weekly_input(report, daily_reports, cards), cards)


# 소수 한 자리 비율(%). 분모가 없으면 None
def _ratio(numerator: int | None, denominator: int | None) -> float | None:
    if numerator is None or not denominator:
        return None
    return round(numerator / denominator * 100, 1)


# DB 보고서 -> 응답 DTO. 섹터 카드의 상승 종목 비율·거래대금 증감률은 여기서 계산한다
def to_response(report: TimelineReport) -> ReportResponse:
    return ReportResponse(
        report_type=report.report_type,
        start_date=report.start_date,
        end_date=report.end_date,
        published_at=report.published_at.replace(tzinfo=_KST) if report.published_at else None,
        title=report.title,
        summary=report.summary,
        main_image_url=report.main_image_url,
        sections=[
            ReportSectionItem(seq=section.seq, title=section.title, description=section.description, image_url=section.image_url, points=[point.body for point in section.points])
            for section in report.sections
        ],
        foreign_net_buy=report.foreign_net_buy,
        institution_net_buy=report.institution_net_buy,
        individual_net_buy=report.individual_net_buy,
        vkospi=report.vkospi,
        vkospi_change_rate=report.vkospi_change_rate,
        quarters=[ReportQuarterItem(label=row.label, usd_krw=row.usd_krw, foreign_net_buy=row.foreign_net_buy, is_current=row.is_current) for row in report.quarters],
        sectors=[
            ReportSectorItem(
                sector_name=row.sector_name,
                change_rate=row.change_rate,
                rising_count=row.rising_count,
                total_count=row.total_count,
                rising_ratio=_ratio(row.rising_count, row.total_count),
                trade_amount=row.trade_amount,
                prev_trade_amount=row.prev_trade_amount,
                trade_amount_change_rate=round((row.trade_amount - row.prev_trade_amount) / row.prev_trade_amount * 100, 1) if row.trade_amount is not None and row.prev_trade_amount else None,
            )
            for row in report.sectors
        ],
        conclusion=report.conclusion,
        keywords=[ReportKeywordItem(title=row.title, description=row.description) for row in report.keywords],
        terms=[ReportTermItem(term=row.term, description=row.description, source=row.source) for row in report.terms],
    )


# 날짜로 보고서 조회 (없으면 None). report_type은 report_repository.DAILY / WEEKLY
async def get_report(session: AsyncSession, report_type: str, target_date: date) -> ReportResponse | None:
    report = await report_repository.load_report(session, report_type, target_date)
    return to_response(report) if report else None


# 20:00 슬롯 저장이 끝나면 timeline_service.run_scheduled_collect가 부른다
# 휴장일이면 아무것도 하지 않는다. 오늘이 그 주 마지막 거래일이면 일간에 이어 주간도 만든다
# 실패해도 예외를 밖으로 내보내지 않는다 (일간이 실패해도 주간은 시도한다 - 그 주 앞선 일간 보고서로 만들 수 있다)
async def run_scheduled_reports() -> None:
    today = datetime.now(_KST).date()
    if not market_hours.is_trading_day(today):
        logger.info("[스케줄러] 보고서 건너뜀 - 오늘은 장이 열리지 않습니다.")
        return

    started = datetime.now(_KST)
    try:
        async with get_session_factory()() as session:
            report = await generate_daily(session, today)
        logger.info(
            "[스케줄러] 일간 보고서 %s 저장 완료 (%.0f초) - 문구 %s, 이미지 %s",
            today, (datetime.now(_KST) - started).total_seconds(), "있음" if report.title else "없음", "있음" if report.main_image_url else "없음",
        )
    except Exception as error:
        logger.error("[스케줄러] 일간 보고서 %s 생성 실패 - %s: %s", today, type(error).__name__, error, exc_info=True)

    trading_days = await asyncio.to_thread(_week_trading_days, today)
    if not trading_days or trading_days[-1] != today:
        return

    started = datetime.now(_KST)
    try:
        async with get_session_factory()() as session:
            report = await generate_weekly(session, today)
        if report is not None:
            logger.info(
                "[스케줄러] 주간 보고서 %s~%s 저장 완료 (%.0f초) - 문구 %s, 이미지 %s",
                report.start_date, report.end_date, (datetime.now(_KST) - started).total_seconds(), "있음" if report.title else "없음", "있음" if report.main_image_url else "없음",
            )
    except Exception as error:
        logger.error("[스케줄러] 주간 보고서 %s 생성 실패 - %s: %s", today, type(error).__name__, error, exc_info=True)
