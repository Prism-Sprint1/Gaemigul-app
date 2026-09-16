# report_service.py
# 일간·주간 보고서를 만든다. 수치 수집(report_data_service) -> LLM 문구 -> 자동 검사(text_review) -> 이미지 -> 저장(report_repository).
#   generate_daily           일간 보고서 생성·저장 (20:00 슬롯 직후, POST /timeline/report/daily)
#   generate_weekly          주간 보고서 생성·저장 (그 주 마지막 거래일 일간 보고서 직후, POST /timeline/report/weekly)
#   get_report               날짜로 보고서 조회 (GET /timeline/report)
#   get_report_list          월별 보고서 목록 - 주 묶음 (GET /timeline/reports)
#   to_response              DB 보고서 -> 응답 DTO (비율·증감률·VKOSPI 뱃지 계산 포함)
#   run_scheduled_reports    20:00 슬롯이 끝나면 timeline_service가 부른다 (휴장일·마지막 거래일 판단 + 실패 로깅)
#
# LLM 문구는 타임라인 브리핑과 같은 원칙으로 만든다
#   먼저 수치를 저장하고, 그 수치를 [확정 수치]로, 타임라인 글·뉴스를 따로 나눠 넘겨 없는 숫자를 만들지 못하게 한다
#   카드·차트 숫자는 LLM이 쓰지 않고 코드가 채운다
# 단계마다 따로 저장하므로 LLM이나 이미지가 실패해도 앞 단계 값은 남는다

import asyncio
import json
import logging
import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core import image_client, llm_client, storage_client
from backend.core.database import get_session_factory
from backend.domain.timeline.models.report import TimelineReport, TimelineReportSector
from backend.domain.timeline.models.timeline import TimelineSlot
from backend.domain.timeline.schemas.report import (
    ReportKeywordItem,
    ReportListItem,
    ReportListResponse,
    ReportQuarterItem,
    ReportResponse,
    ReportSectionItem,
    ReportSectorItem,
    ReportTermItem,
    ReportWeekGroup,
)
from backend.domain.timeline.services import glossary, market_hours, prompts, report_data_service, report_repository, text_review, timeline_repository

_KST = ZoneInfo("Asia/Seoul")

logger = logging.getLogger(__name__)

# 섹션·핵심 요약·키워드·용어 개수. 바꾸면 저장 개수가 바뀐다 (프롬프트 [길이]·[출력 형식]도 같이 맞출 것)
_SECTION_COUNT = 3
_POINT_COUNT = 3
_KEYWORD_COUNT = 3
_TERM_COUNT = 3

# 보고서 문구 모델. 보고서는 하루 1~2회라 기본 모델(flash-lite)보다 사실 오류가 적은 모델을 쓴다 (무료 하루 20회 - 해설 8회와 나눠 쓴다)
# 이 모델이 실패하면(한도 초과 등) 기본 모델로 한 번 더 만든다. None이면 처음부터 기본 모델
_REPORT_MODEL = "gemini-3.6-flash"

# 이미지 한 장에 넣는 원인 소재 수, LLM이 목록에 없는 흐름·분위기를 냈을 때 대신 쓸 값 (prompts.IMAGE_FLOWS·IMAGE_MOODS의 키)
_IMAGE_SYMBOL_COUNT = 2
_DEFAULT_IMAGE_FLOW = "없음"
_DEFAULT_IMAGE_MOOD = "보합"

# 이미지를 올릴 Supabase Storage 공개 버킷
_IMAGE_BUCKET = "report-images"

# DB 칼럼 길이 (models/report.py와 같게). LLM이 길이 제한을 어겨도 저장이 실패하지 않게 자른다
_MAX_TITLE = 200
_MAX_SUMMARY = 300
_MAX_SHORT = 100


# 백만원 -> "2조 2,984억원" 같은 읽기 쉬운 금액 (LLM 입력용. LLM이 단위를 잘못 옮기지 않게 코드가 바꾼다). 부호는 붙이지 않는다
def _amount(million: int | None) -> str | None:
    if million is None:
        return None
    eok = round(abs(million) / 100)
    jo, rest = divmod(eok, 10000)
    if jo and rest:
        return f"{jo}조 {rest:,}억원"
    if jo:
        return f"{jo}조원"
    return f"{rest:,}억원"


# 순매수 금액(백만원, 음수면 순매도) -> "2조 2,984억원 순매도" (부호 대신 방향 단어. "-2조원 순매도" 같은 이중 표현을 막는다)
def _flow(million: int | None) -> str | None:
    if million is None:
        return None
    if million == 0:
        return "0원"
    return f"{_amount(million)} {'순매도' if million < 0 else '순매수'}"


# 증감 문자열 "30% 증가" / "12% 감소" (전일·전주 대비 거래대금). 부호 대신 방향 단어. 비교값이 없으면 None
def _change_percent(current: int | None, previous: int | None) -> str | None:
    if not current or not previous:
        return None
    rate = (current - previous) / previous * 100
    return f"{abs(rate):.0f}% {'증가' if rate >= 0 else '감소'}"


# 섹터 카드 dict -> LLM 입력용 확정 수치
def _sector_fact(card: dict) -> dict:
    fact = {"업종": card["sector_name"], "등락률(%)": card.get("change_rate"), "거래대금": _amount(card.get("trade_amount")), "거래대금 증감": _change_percent(card.get("trade_amount"), card.get("prev_trade_amount"))}
    if card.get("rising_count") is not None and card.get("total_count"):
        fact["상승 종목"] = f"{card['total_count']}개 중 {card['rising_count']}개"
    return {key: value for key, value in fact.items() if value is not None}


# 보고서 수치 -> LLM 입력용 확정 수치 (투자자 순매수·VKOSPI·분기 차트)
def _report_facts(report: TimelineReport) -> dict:
    facts = {
        "코스피 외국인 매매": _flow(report.foreign_net_buy),
        "코스피 기관 매매": _flow(report.institution_net_buy),
        "코스피 개인 매매": _flow(report.individual_net_buy),
        "외국인 순매수 흐름": report.foreign_badge,
        "VKOSPI": report.vkospi,
        "VKOSPI 등락률(%)": report.vkospi_change_rate,
        "분기별 원달러 환율·외국인 매매": [
            {"분기": quarter.label + (" (진행 중)" if quarter.is_current else ""), "환율": quarter.usd_krw, "외국인 매매": _flow(quarter.foreign_net_buy)}
            for quarter in report.quarters
        ],
    }
    return {key: value for key, value in facts.items() if value not in (None, "", [])}


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


# 일간 보고서 재료 JSON. 확정 수치(보고서 수치 + 업종 등락 분포 + 타임라인 시세) / 타임라인(슬롯 브리핑) / 뉴스(슬롯 뉴스, 링크 중복 제거)
def _daily_input(report: TimelineReport, slots: list[TimelineSlot], cards: list[dict], breadth: dict | None) -> str:
    facts = _report_facts(report)
    if cards:
        facts["주목할 섹터 (그날 종가 기준 코스피 업종 등락률 1위)"] = _sector_fact(cards[0])
    if breadth:
        facts["코스피 업종 등락 (그날 종가 기준, 업종 수)"] = breadth

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
    payload = {"확정 수치": {key: value for key, value in facts.items() if value not in (None, "", [])}, "타임라인": timeline, "뉴스": news}
    return json.dumps(payload, ensure_ascii=False, indent=2)


# 주간 보고서 재료 JSON. 확정 수치(주간 수치 + 일별 외국인 매매 + 주목할 섹터 주간 값) / 일간 보고서(문구)
def _weekly_input(report: TimelineReport, daily_reports: list[TimelineReport], cards: list[dict], breadth: dict | None) -> str:
    facts = _report_facts(report)
    # 주간 합계임을 LLM이 알도록 이름을 바꾼다
    for key in ("코스피 외국인 매매", "코스피 기관 매매", "코스피 개인 매매"):
        if key in facts:
            facts[f"{key} (주간 합계)"] = facts.pop(key)
    if "VKOSPI 등락률(%)" in facts:
        facts["VKOSPI 전주 대비 등락률(%)"] = facts.pop("VKOSPI 등락률(%)")
    facts["일별 외국인 매매"] = [{"날짜": f"{daily.start_date:%m-%d}", "외국인 매매": _flow(daily.foreign_net_buy)} for daily in daily_reports if daily.foreign_net_buy is not None]
    if cards:
        facts["주목할 섹터 (주간 등락률 1위, 주간 거래대금·전주 대비)"] = _sector_fact(cards[0])
    if breadth:
        facts["코스피 업종 등락 (주간, 업종 수)"] = breadth

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
    payload = {"확정 수치": {key: value for key, value in facts.items() if value not in (None, "", [])}, "일간 보고서": dailies}
    return json.dumps(payload, ensure_ascii=False, indent=2)


# 문자열 값을 꺼내 다듬는다 (없거나 문자열이 아니면 빈 문자열). LLM 문구는 전부 여기를 거친다 ("퍼센트" -> "%" 포함)
def _text(value, limit: int | None = None) -> str:
    text = text_review.normalize_percent(value.strip()) if isinstance(value, str) else ""
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
    if len(keywords) < _KEYWORD_COUNT:
        logger.warning("보고서 결론 영역 섹션별 요약이 %d개만 왔습니다 (섹션과 순서가 어긋날 수 있다).", len(keywords))

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


# 보고서 문구를 재료와 대조해 자동 검사한다 (text_review.check - 비교 표현 삭제, 자료에 없는 숫자 등은 WARNING 로그)
def _check_content(report_type: str, start_date: date, data: str, content: dict) -> dict:
    return text_review.check(f"{report_type} {start_date} 보고서", content, data)


# LLM으로 보고서 문구를 만든다 (동기). 실패하면 None
# _REPORT_MODEL로 먼저 만들고, 호출이 실패하거나 필요한 값이 빠지면 기본 모델로 한 번 더 만든다
# 반환: {"content": save_report_content 형식, "main_scene", "section1_scene"}
def _generate_content(report_type: str, start_date: date, end_date: date, data: str, sector: str) -> dict | None:
    prompt = prompts.REPORT_PROMPT.format(
        period=prompts.REPORT_PERIOD[report_type],
        image_symbols="\n".join(f"- {name}" for name in prompts.IMAGE_SYMBOLS),
        image_flows="\n".join(f"- {name}" for name in prompts.IMAGE_FLOWS),
        image_moods="\n".join(f"- {name}" for name in prompts.IMAGE_MOODS),
        start_date=start_date,
        end_date=end_date,
        sector=sector,
        data=data,
    )
    answer, content = None, None
    for model in dict.fromkeys([_REPORT_MODEL or llm_client.DEFAULT_MODEL, llm_client.DEFAULT_MODEL]):
        try:
            answer = llm_client.generate_json(prompt, timeout=180.0, model=model)
        except (RuntimeError, ValueError, KeyError, httpx.HTTPError) as error:
            logger.warning("%s %s 보고서 문구 생성 실패 (%s) - %s: %s", report_type, start_date, model, type(error).__name__, error)
            continue
        content = _parse_content(answer)
        if content is not None:
            break
        logger.warning("%s %s 보고서 응답에 필요한 값이 없습니다 (%s).", report_type, start_date, model)
    if content is None:
        return None

    content = _check_content(report_type, start_date, data, content)
    content["terms"] = _pick_terms(content, answer.get("terms") or [])
    return {
        "content": content,
        "main_scene": _image_scene(answer.get("main_image"), f"{report_type} {start_date} main", content["summary"], role="main"),
        "section1_scene": _image_scene(answer.get("section1_image"), f"{report_type} {start_date} section1", content["sections"][0]["description"], role="section1"),
        "main_annotations": _image_annotations(answer.get("main_image"), content["summary"], content["title"], role="main"),
        "section1_annotations": _image_annotations(answer.get("section1_image"), content["sections"][0]["description"], content["sections"][0]["title"], role="section1"),
    }


# 문구에서 코스피의 직접적인 등락 표현만 찾는다. 모호하거나 상반되면 방향을 그리지 않는다.
# 한국어 원문·양방향 예시를 이미지 모델에 보내지 않고 확정한 영어 지시 하나만 보낸다.
def _image_market_direction(source_text: str) -> str | None:
    matches = re.findall(
        r"(?:코스피|KOSPI)(?:지수| 지수)?(?:가|는|은|도)?\s*"
        r"(?:[0-9.,%]+|포인트|넘게|넘는|이상|이하|가까이|약|대|큰\s*폭으로|소폭|크게|\s){0,30}"
        r"(하락|급락|내렸|떨어졌|상승|급등|올랐)",
        source_text, re.IGNORECASE,
    )
    directions = {"down" if value in {"하락", "급락", "내렸", "떨어졌"} else "up" for value in matches}
    return next(iter(directions)) if len(directions) == 1 else None


# 원문에 있는 표현만 짧은 한글 라벨로 쓴다. 근거가 없으면 방향 없는 소재명으로 둔다.
def _image_prop_label(name: str, source_text: str) -> str:
    if name == "금리·연준·중앙은행":
        if "금리 인상 우려" in source_text:
            return "금리 우려"
        return "금리"
    if name == "유가·원유":
        if re.search(r"(?:국제)?유가(?:가|는|의)?\s*(?:상승|급등)", source_text):
            return "유가 상승"
        if re.search(r"(?:국제)?유가(?:가|는|의)?\s*(?:하락|급락)", source_text):
            return "유가 하락"
        return "유가"
    return {"인공지능(AI)": "인공지능", "환율·달러": "환율", "국채·채권": "국채"}.get(name, name.split("·")[0])


def _image_annotations(plan, source_text: str, headline: str, *, role: str = "main") -> dict:
    plan = plan if isinstance(plan, dict) else {}
    names = list(dict.fromkeys(name for name in (plan.get("symbols") or []) if name in prompts.IMAGE_SYMBOLS))[:_IMAGE_SYMBOL_COUNT]
    labels = []
    direction = _image_market_direction(source_text)
    if role == "main" and direction:
        labels.append("코스피 하락" if direction == "down" else "코스피 상승")
    if role != "main":
        labels.extend(_image_prop_label(name, source_text) for name in names)
    flow = plan.get("flow")
    if role == "main" and flow in {"외국인 매도", "외국인 매수"}:
        labels.append(flow)
    return {"headline": headline, "labels": list(dict.fromkeys(labels))[:4]}


# 기존 LLM의 소재·흐름·분위기 키 유지. Pollinations에는 글자 없는 영어 장면만 보내며 추가 LLM 호출은 없다.
def _image_scene(plan, label: str, source_text: str = "", *, role: str = "main") -> str:
    plan = plan if isinstance(plan, dict) else {}
    picked = [name for name in plan.get("symbols") or [] if isinstance(name, str)]
    names = list(dict.fromkeys(name for name in picked if name in prompts.IMAGE_SYMBOLS))[:_IMAGE_SYMBOL_COUNT]
    # 메인은 시장 결과와 자금 흐름, 섹션1은 원인 분석을 맡는다. 같은 원인 소품을 두 장에 반복하지 않는다.
    scene_names = [] if role == "main" else names
    flow, mood = plan.get("flow"), plan.get("mood")
    if len(names) < len(picked) or flow not in prompts.IMAGE_FLOWS or mood not in prompts.IMAGE_MOODS:
        logger.warning("%s 이미지 재료에 목록에 없는 이름이 있습니다 - 소재 %s, 흐름 %s, 분위기 %s", label, picked, flow, mood)
    values = {
        "city": prompts.IMAGE_CITY,
        "mood": prompts.IMAGE_MOODS.get(mood, prompts.IMAGE_MOODS[_DEFAULT_IMAGE_MOOD]),
        "flow": prompts.IMAGE_FLOWS.get(flow, prompts.IMAGE_FLOWS[_DEFAULT_IMAGE_FLOW]) if role == "main" else prompts.IMAGE_FLOWS[_DEFAULT_IMAGE_FLOW],
        "causes": " and ".join(prompts.IMAGE_SYMBOLS[name] for name in scene_names),
    }
    scene = (prompts.IMAGE_SCENE if scene_names else prompts.IMAGE_SCENE_NO_CAUSE).format(**values)
    direction = _image_market_direction(source_text) if role == "main" else None
    if direction == "down":
        scene += " On the wall behind the main person, one wooden frame contains exactly ONE thick RED zigzag arrow descending from upper left to lower right, ending at the bottom right. The main person looks mildly worried. This single red arrow is the only saturated color. The panel has a plain cream surface with no grid or writing."
    elif direction == "up":
        scene += " On the wall behind the main person, one wooden frame contains exactly ONE thick BLUE zigzag arrow ascending from lower left to upper right, ending at the top right. The main person looks gently hopeful. This single blue arrow is the only saturated color. The panel has a plain cream surface with no grid or writing."
    else:
        scene += ' No market chart or colored arrow; keep the entire scene in neutral tones.'
    if role == "main":
        scene += " Compose this as a wide whole-market overview: the market outcome, central investor, wall arrow and doorway money flow are the visual story."
    else:
        scene += (
            " Compose this as a close cause-explanation workshop, clearly different from a whole-market overview. "
            "Place the main person at the right third, actively examining the economic cause props on a workbench at the left. "
            "Show the cause props larger and more concrete. No doorway, no secondary investor, no suitcase, no money-flow arrow and no market-direction chart."
        )
    if re.search(r"의료[·ㆍ\s]*정밀|의료기기|의료·정밀기기", source_text):
        scene += " A small neutral-gray microscope and caliper on a subordinate shelf represent medical precision instruments."
    return scene


# 그림 설명으로 이미지를 만들어 올리고 공개 URL을 돌려준다 (동기). 실패하면 None
# 경로에 생성 시각을 넣는다 - 같은 경로에 덮어쓰면 CDN 캐시 때문에 한동안 옛 이미지가 보인다
def _make_image(scene: str, report_type: str, start_date: date, name: str, annotations: dict | None = None) -> str | None:
    if not scene:
        logger.warning("%s %s %s 이미지 그림 설명이 없어 건너뜁니다.", report_type, start_date, name)
        return None
    try:
        image = image_client.generate_image(f"{scene}, {prompts.IMAGE_STYLE}")
        if annotations:
            image = image_client.add_korean_labels(image, headline=annotations["headline"], labels=annotations["labels"])
        extension, content_type = image_client.image_format(image)
        path = f"{report_type.lower()}/{start_date}/{name}_{datetime.now(_KST):%H%M%S_%f}.{extension}"
        return storage_client.upload_file(_IMAGE_BUCKET, path, image, content_type)
    except (RuntimeError, KeyError, ValueError, httpx.HTTPError) as error:
        logger.warning("%s %s %s 이미지 생성·업로드 실패 - %s: %s", report_type, start_date, name, type(error).__name__, error)
        return None


# 문구 저장 -> 이미지 저장 (일간·주간 공통 뒷부분)
#   report  수치(섹터 카드 포함)까지 저장된 보고서
# 문구 생성이 실패하면 기존 문구를 그대로 두고 돌려준다
async def _write_report(session: AsyncSession, report: TimelineReport, data: str) -> TimelineReport:
    report_type, start_date, end_date = report.report_type, report.start_date, report.end_date
    sector = report.sectors[0].sector_name if report.sectors else "(없음)"
    generated = await asyncio.to_thread(_generate_content, report_type, start_date, end_date, data, sector)
    if generated is None:
        return report

    await report_repository.save_report_content(session, report_type, start_date, generated["content"])

    # 생성 서비스의 요청 한도를 고려해 두 장을 순차 생성한다
    main_url = await asyncio.to_thread(_make_image, generated["main_scene"], report_type, start_date, "main", generated["main_annotations"])
    section1_url = await asyncio.to_thread(_make_image, generated["section1_scene"], report_type, start_date, "section1", generated["section1_annotations"])
    return await report_repository.save_report_images(session, report_type, start_date, main_image_url=main_url, section1_image_url=section1_url)


# 일간 보고서를 만들어 저장한다. day를 비우면 오늘(한국 시간)
# 순서: 수치 수집·저장(섹터 카드 = 그날 종가 기준 업종 등락률 1위) -> 그날 타임라인 슬롯 읽기 -> 문구 -> 자동 검사 -> 이미지
async def generate_daily(session: AsyncSession, day: date | None = None) -> TimelineReport:
    day = day or datetime.now(_KST).date()

    report, breadth = await report_data_service.collect_and_save_daily(session, day)
    cards = [_card_from_row(row) for row in report.sectors]
    slots = await timeline_repository.load_day(session, day)
    if not slots:
        logger.warning("일간 보고서 %s - 그날 타임라인 슬롯이 없습니다. 수치만으로 문구를 만듭니다.", day)

    return await _write_report(session, report, _daily_input(report, slots, cards, breadth))


# day가 속한 주(월~금)의 거래일 목록
def _week_trading_days(day: date) -> list[date]:
    monday = day - timedelta(days=day.weekday())
    return [monday + timedelta(days=offset) for offset in range(5) if market_hours.is_trading_day(monday + timedelta(days=offset))]


# 주간 보고서를 만들어 저장한다. day가 속한 주가 대상이다 (비우면 오늘)
# 재료는 그 주 일간 보고서다. 일간 보고서가 하나도 없으면 만들지 않고 None
# 섹터 카드는 코스피 업종 중 그 주 등락률 1위 업종 하나다
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

    data = await asyncio.to_thread(report_data_service.collect_weekly_data, start_date, end_date)
    cards, breadth = await asyncio.to_thread(report_data_service.collect_weekly_top_sector, start_date, end_date)
    if cards:
        data["sectors"] = cards

    report = await report_repository.save_report_data(session, report_repository.WEEKLY, start_date, end_date, data)
    return await _write_report(session, report, _weekly_input(report, daily_reports, cards, breadth))


# VKOSPI 등락률 -> 카드 뱃지 "+18.2% 급등". 등락률이 없으면 None
# 기준을 바꾸려면 _VKOSPI_SURGE(급등·급락 경계, %)를 고친다. 0이면 보합
_VKOSPI_SURGE = 10.0


def _vkospi_badge(change_rate: float | None) -> str | None:
    if change_rate is None:
        return None
    change_rate = round(change_rate, 1)  # 화면에 보이는 숫자로 단어를 정한다 (9.99를 "+10.0% 상승"으로 쓰지 않도록)
    if change_rate >= _VKOSPI_SURGE:
        word = "급등"
    elif change_rate > 0:
        word = "상승"
    elif change_rate == 0:
        word = "보합"
    elif change_rate > -_VKOSPI_SURGE:
        word = "하락"
    else:
        word = "급락"
    return f"{change_rate:+.1f}% {word}"


# 소수 한 자리 비율(%). 분모가 없으면 None
def _ratio(numerator: int | None, denominator: int | None) -> float | None:
    if numerator is None or not denominator:
        return None
    return round(numerator / denominator * 100, 1)


# 섹터 행 -> 응답 카드. 상승 종목 비율·거래대금 증감률을 여기서 계산한다
def _sector_item(row: TimelineReportSector) -> ReportSectorItem:
    return ReportSectorItem(
        sector_name=row.sector_name,
        change_rate=row.change_rate,
        rising_count=row.rising_count,
        total_count=row.total_count,
        rising_ratio=_ratio(row.rising_count, row.total_count),
        trade_amount=row.trade_amount,
        prev_trade_amount=row.prev_trade_amount,
        trade_amount_change_rate=_ratio(row.trade_amount - row.prev_trade_amount, row.prev_trade_amount) if row.trade_amount is not None and row.prev_trade_amount else None,
    )


# DB 보고서 -> 응답 DTO
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
        foreign_badge=report.foreign_badge,
        vkospi=report.vkospi,
        vkospi_change_rate=report.vkospi_change_rate,
        vkospi_badge=_vkospi_badge(report.vkospi_change_rate),
        quarters=[ReportQuarterItem(label=row.label, usd_krw=row.usd_krw, foreign_net_buy=row.foreign_net_buy, is_current=row.is_current) for row in report.quarters],
        sector=_sector_item(report.sectors[0]) if report.sectors else None,
        conclusion=report.conclusion,
        keywords=[ReportKeywordItem(title=row.title, description=row.description) for row in report.keywords],
        terms=[ReportTermItem(term=row.term, description=row.description) for row in report.terms],
    )


# 날짜로 보고서 조회 (없으면 None). report_type은 report_repository.DAILY / WEEKLY
async def get_report(session: AsyncSession, report_type: str, target_date: date) -> ReportResponse | None:
    report = await report_repository.load_report(session, report_type, target_date)
    return to_response(report) if report else None


# ORM 보고서 -> 목록 카드
def _list_item(report: TimelineReport) -> ReportListItem:
    return ReportListItem(report_type=report.report_type, start_date=report.start_date, end_date=report.end_date, title=report.title, summary=report.summary)


# 월별 보고서 목록 (브리핑 탭 우측 목록). 주(월~금) 단위로 묶는다
#   주가 속한 달 = 그 주 월요일이 속한 달 (9/28~10/2 주는 9월 목록, 10/5 주부터 10월)
#   주차 = 그 달의 몇 번째 월요일인지 (9/28 → 9월 4주차)
#   묶음 범위 = 그 주 거래일만 (추석처럼 휴장일이 있으면 "9.21 - 9.23")
#   보고서가 하나도 없는 주, 문구가 없는(LLM 실패) 보고서는 뺀다
#   정렬: 최신 주가 먼저, 주 안의 일간은 날짜순 (주간은 weekly 칸). 주 순서를 바꾸려면 sorted의 reverse를 고친다
async def get_report_list(session: AsyncSession, year: int, month: int) -> ReportListResponse:
    first_day = date(year, month, 1)
    first_monday = first_day + timedelta(days=(7 - first_day.weekday()) % 7)
    last_day = date(year + (month == 12), month % 12 + 1, 1) - timedelta(days=1)
    last_monday = last_day - timedelta(days=last_day.weekday())

    by_monday: dict[date, list[TimelineReport]] = {}
    for report in await report_repository.load_reports_between(session, first_monday, last_monday + timedelta(days=4)):
        if report.title:
            by_monday.setdefault(report.start_date - timedelta(days=report.start_date.weekday()), []).append(report)

    weeks = []
    for monday in sorted(by_monday, reverse=True):
        reports = by_monday[monday]
        trading_days = await asyncio.to_thread(_week_trading_days, monday) or sorted(report.start_date for report in reports)
        week_of_month = (monday.day - 1) // 7 + 1
        weekly = next((report for report in reports if report.report_type == report_repository.WEEKLY), None)
        weeks.append(
            ReportWeekGroup(
                year=monday.year,
                month=monday.month,
                week_of_month=week_of_month,
                week_label=f"{monday.month}월 {week_of_month}주차",
                start_date=trading_days[0],
                end_date=trading_days[-1],
                weekly=_list_item(weekly) if weekly else None,
                dailies=[_list_item(report) for report in sorted(reports, key=lambda report: report.start_date) if report.report_type == report_repository.DAILY],
            )
        )
    return ReportListResponse(year=year, month=month, weeks=weeks)


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
