# timeline.py
# timeline 도메인의 API 엔드포인트. 실제 처리는 services에 있고 여기서는 연결만 한다.

from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db

from backend.domain.timeline.schemas.market_indicator import IndicatorBarResponse
from backend.domain.timeline.schemas.report import ReportResponse
from backend.domain.timeline.schemas.timeline import TimelineSlotResponse
from backend.domain.timeline.services import glossary, market_indicator_service, report_repository, report_service, timeline_service

_KST = ZoneInfo("Asia/Seoul")

router = APIRouter(prefix="/timeline", tags=["timeline"])


# GET /timeline/indicators - 최상단 지표 바. 캐시만 읽는다
@router.get("/indicators", response_model=IndicatorBarResponse)
def get_indicators() -> IndicatorBarResponse:
    return market_indicator_service.get_indicators()


# GET /timeline/slots - 슬롯 목록 [{slot_key, time_slot, title}]
@router.get("/slots")
def get_slot_list() -> list[dict]:
    return timeline_service.get_slot_list()


# GET /timeline/glossary - 용어 사전 {용어: 설명}. 프런트 호버 설명용
@router.get("/glossary")
def get_glossary() -> dict[str, str]:
    return glossary.GLOSSARY


# GET /timeline/slot/{slot_key} - 저장 없이 즉석 수집 (확인용, 화면용 아님)
# slot_key는 "0730"처럼 콜론 없이. ?with_briefing=false면 LLM을 건너뛴다. 없는 슬롯이면 404
@router.get("/slot/{slot_key}", response_model=TimelineSlotResponse)
def get_slot(slot_key: str, with_briefing: bool = True) -> TimelineSlotResponse:
    try:
        return timeline_service.get_slot(slot_key, with_briefing=with_briefing)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


# GET /timeline?date=2026-09-14 - 하루치 슬롯 (프런트용). date를 빼면 오늘
# DB에서 읽기만 한다. 오늘이면 슬롯 시각이 지난 슬롯만 나온다
@router.get("", response_model=list[TimelineSlotResponse])
async def get_day(date_: date | None = Query(default=None, alias="date"), session: AsyncSession = Depends(get_db)) -> list[TimelineSlotResponse]:
    return await timeline_service.get_day(session, date_ or datetime.now(_KST).date())


# POST /timeline/collect/{slot_key} - 슬롯을 수집해서 DB에 저장 (스케줄러 동작을 수동 실행)
# 같은 날 같은 슬롯이 있으면 덮어쓴다. ?with_briefing=false면 LLM 생략, ?trade_date=로 날짜 지정
@router.post("/collect/{slot_key}", response_model=TimelineSlotResponse)
async def collect_slot(slot_key: str, with_briefing: bool = True, trade_date: date | None = None, session: AsyncSession = Depends(get_db)) -> TimelineSlotResponse:
    try:
        return await timeline_service.collect_and_save(session, slot_key, trade_date=trade_date, with_briefing=with_briefing)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


# 보고서 종류 쿼리 값 -> DB 값. 키를 바꾸면 프런트가 보내는 type 값이 바뀐다
_REPORT_TYPES = {"daily": report_repository.DAILY, "weekly": report_repository.WEEKLY}


# GET /timeline/report?type=daily&date=2026-09-14 - 보고서 (프런트용). date를 빼면 오늘
# 일간은 그날 보고서, 주간은 그 날짜가 속한 주의 보고서. 없으면 null
# DB에서 읽기만 한다
@router.get("/report", response_model=ReportResponse | None)
async def get_report(type_: str = Query(alias="type"), date_: date | None = Query(default=None, alias="date"), session: AsyncSession = Depends(get_db)) -> ReportResponse | None:
    if type_ not in _REPORT_TYPES:
        raise HTTPException(status_code=404, detail=f"'{type_}'는 없는 보고서 종류입니다. 가능한 값: {', '.join(_REPORT_TYPES)}")
    return await report_service.get_report(session, _REPORT_TYPES[type_], date_ or datetime.now(_KST).date())


# POST /timeline/report/daily?date=2026-09-14 - 일간 보고서 생성·저장 (스케줄러 동작을 수동 실행). date를 빼면 오늘
# 같은 날 보고서가 있으면 고쳐 쓴다. LLM·이미지 포함 1분 안팎 걸린다
# 주의: 섹터 카드의 상승 종목 수는 그날 다음 개장 전까지만 채워진다
@router.post("/report/daily", response_model=ReportResponse)
async def create_daily_report(date_: date | None = Query(default=None, alias="date"), session: AsyncSession = Depends(get_db)) -> ReportResponse:
    return report_service.to_response(await report_service.generate_daily(session, date_))


# POST /timeline/report/weekly?date=2026-09-14 - date가 속한 주의 주간 보고서 생성·저장. date를 빼면 이번 주
# 그 주 일간 보고서가 없으면 404
@router.post("/report/weekly", response_model=ReportResponse)
async def create_weekly_report(date_: date | None = Query(default=None, alias="date"), session: AsyncSession = Depends(get_db)) -> ReportResponse:
    report = await report_service.generate_weekly(session, date_)
    if report is None:
        raise HTTPException(status_code=404, detail="그 주의 일간 보고서가 없어 주간 보고서를 만들 수 없습니다.")
    return report_service.to_response(report)
