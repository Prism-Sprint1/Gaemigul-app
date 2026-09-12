# timeline.py
# 엔드 포인트 및 URL 주소 매핑

from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db

from backend.domain.timeline.schemas.market_indicator import IndicatorBarResponse
from backend.domain.timeline.schemas.timeline import TimelineSlotResponse
from backend.domain.timeline.services import glossary, market_indicator_service, timeline_service

_KST = ZoneInfo("Asia/Seoul")

router = APIRouter(prefix="/timeline", tags=["timeline"])


# 최상단 지표 바 데이터 조회
# 캐시에서 바로 읽기 때문에 이 요청 자체는 KIS를 호출하지 않는다
@router.get("/indicators", response_model=IndicatorBarResponse)
def get_indicators() -> IndicatorBarResponse:
    return market_indicator_service.get_indicators()


# 호출 가능한 슬롯 목록 조회 (어떤 slot_key를 쓰면 되는지 확인용)
@router.get("/slots")
def get_slot_list() -> list[dict]:
    return timeline_service.get_slot_list()


# 주식 입문자용 용어 사전 조회 ({용어: 설명})
#
# 불개미 해설 본문에는 용어 설명이 들어가지 않는다(프롬프트에서 금지했다). 대신 프런트가
# 이 표를 받아서, 본문에 나온 용어에 마우스를 올리면 설명이 뜨게 처리한다.
# 설명을 LLM이 만들지 않고 우리가 정해두는 이유는 services/glossary.py 주석에 적어뒀다
@router.get("/glossary")
def get_glossary() -> dict[str, str]:
    return glossary.GLOSSARY


# 슬롯 하나를 즉석 수집해서 조회 (확인용. DB에 저장하지 않는다)
# slot_key는 콜론 없이 4자리로 받는다 - URL에 콜론을 쓸 수 없어서다 (예: /timeline/slot/0730)
#
# 화면용이 아니다. 요청이 올 때마다 KIS·네이버를 새로 호출하므로 부를 때마다 값이 조금씩
# 달라진다(장중이면 특히). 프런트는 GET /timeline을 쓴다
#
# with_briefing=false를 붙이면 LLM 단계를 건너뛴다 (예: /timeline/slot/0730?with_briefing=false)
# LLM을 세 번 부르면 1~2분 걸려서, 수집 결과만 빠르게 볼 때 쓴다
@router.get("/slot/{slot_key}", response_model=TimelineSlotResponse)
def get_slot(slot_key: str, with_briefing: bool = True) -> TimelineSlotResponse:
    try:
        return timeline_service.get_slot(slot_key, with_briefing=with_briefing)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


# 하루치 타임라인 조회 (프런트가 쓰는 엔드포인트)
# date를 안 주면 오늘. 예: /timeline?date=2026-09-11
#
# DB에서 읽기만 하므로 즉시 응답한다. 수집은 스케줄러가 미리 해둔다.
# 오늘 날짜를 조회하면 아직 시간이 안 된 슬롯은 빠진다
# 슬롯 시각에 수집을 시작해서 1~2분 뒤에 저장되므로, 슬롯은 시각이 조금 지난 뒤에 나타난다
@router.get("", response_model=list[TimelineSlotResponse])
async def get_day(date_: date | None = Query(default=None, alias="date"), session: AsyncSession = Depends(get_db)) -> list[TimelineSlotResponse]:
    return await timeline_service.get_day(session, date_ or datetime.now(_KST).date())


# 슬롯 하나를 수집해서 DB에 저장 (스케줄러가 부를 동작을 수동으로 실행하는 용도)
# 같은 날 같은 시간대가 이미 있으면 지우고 새로 넣는다
#
# 조회가 아니라 데이터를 만드는 동작이라 POST로 뒀다
# LLM 때문에 1분 안팎 걸린다. with_briefing=false를 붙이면 LLM을 건너뛴다
@router.post("/collect/{slot_key}", response_model=TimelineSlotResponse)
async def collect_slot(slot_key: str, with_briefing: bool = True, trade_date: date | None = None, session: AsyncSession = Depends(get_db)) -> TimelineSlotResponse:
    try:
        return await timeline_service.collect_and_save(session, slot_key, trade_date=trade_date, with_briefing=with_briefing)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
