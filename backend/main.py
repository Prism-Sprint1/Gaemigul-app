# main.py
# FastAPI 앱 진입점. 로그 설정, 스케줄러(지표 바 갱신 1개 + 슬롯 수집 8개), CORS, 라우터 등록.
# 보고서는 따로 예약하지 않는다. 20:00 슬롯 작업이 끝나면 timeline_service가 이어서 만든다

import logging
from contextlib import asynccontextmanager
from datetime import datetime
import logging
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

<<<<<<< HEAD
from backend.core.config import get_settings
from backend.core.logging_config import setup_logging
from backend.domain.timeline.routers.timeline import router as timeline_router
from backend.domain.timeline.services import market_indicator_service, timeline_service

logger = logging.getLogger(__name__)

# 예약 작업 스케줄러 (한국 시간 기준)
# AsyncIOScheduler는 서버의 이벤트 루프에서 돌아 async 함수를 실행할 수 있다. 서버가 떠 있을 때만 동작한다
# misfire_grace_time: 예약 시각보다 이 초만큼 늦어도 실행한다. 늘리면 맥이 잠들었다 깬 뒤에도
#   지난 슬롯이 실행되는데, 그러면 그 시각이 아닌 값이 저장되므로 짧게 둔다
_scheduler = AsyncIOScheduler(timezone=ZoneInfo("Asia/Seoul"), job_defaults={"misfire_grace_time": 10})
=======
from backend.domain.calendar.routers.calendar import router as calendar_router
from backend.domain.timeline.routers.timeline import router as timeline_router
from backend.domain.timeline.services import market_indicator_service
from backend.core.config import get_settings
from backend.domain.heatmap.routers.heatmap import router as heatmap_router
from backend.domain.heatmap.services import heatmap

# minute="0,30" -> 매 시 0분/30분에 실행. 이 값을 바꾸면 갱신 주기가 바뀐다(예: "0,15,30,45"면 15분마다).
_KST = ZoneInfo("Asia/Seoul")
_logger = logging.getLogger(__name__)


def _refresh_indicators(*, force: bool = False) -> None:
    # 외부 시세 장애가 앱 시작 자체를 막지 않도록 기존 지표 수집도 백그라운드에서 실행.
    try:
        market_indicator_service.refresh_all(force=force)
    except Exception:
        _logger.exception("시장 지표 갱신 실패: 마지막 수집값을 유지합니다.")
>>>>>>> 417a5403824a674ccf01b6c32189b97a377db9be


# 서버 시작·종료 시 실행
@asynccontextmanager
async def lifespan(app: FastAPI):
<<<<<<< HEAD
    # 로그 설정을 가장 먼저 한다 (작업 등록 중 경고도 파일에 남도록)
    setup_logging()

    _register_indicator_job()
    _register_slot_jobs()

    jobs = _scheduler.get_jobs()
    if jobs:
        _scheduler.start()
        logger.info("스케줄러 시작 - 작업 %d개 (%s)", len(jobs), ", ".join(job.id for job in jobs))
    else:
        logger.warning("등록된 예약 작업이 없습니다. .env의 KIS 키와 DATABASE_URL을 확인해주세요.")

    yield

    if _scheduler.running:
        _scheduler.shutdown()
        logger.info("스케줄러 종료")


# 지표 바 갱신 작업 등록 (10분마다). minute 값을 바꾸면 주기가 바뀐다 (예: "0,30"이면 30분마다)
# 등록 전에 캐시를 한 번 채운다. 실패하면(키 없음·KIS 장애) 지표 바만 끄고 서버는 뜬다
def _register_indicator_job() -> None:
    try:
        market_indicator_service.refresh_all(force=True)
    except Exception as error:
        logger.warning("지표 바 비활성화 - %s: %s", type(error).__name__, error)
        return

    _scheduler.add_job(market_indicator_service.refresh_all, CronTrigger(minute="0,10,20,30,40,50"), id="indicator_bar")


# 슬롯 수집 작업 등록 (하루 8회). 시각은 timeline_service.SLOT_COLLECT_TIMES에서 바꾼다
# DATABASE_URL이 없으면 등록하지 않는다. 휴장일 판단은 작업 안에서 한다
def _register_slot_jobs() -> None:
    if not get_settings().database_url:
        logger.warning("타임라인 슬롯 수집 비활성화 - DATABASE_URL이 .env에 없습니다.")
        return

    for slot_key, (hour, minute) in timeline_service.SLOT_COLLECT_TIMES.items():
        _scheduler.add_job(
            timeline_service.run_scheduled_collect,
            CronTrigger(hour=hour, minute=minute),
            args=[slot_key],
            id=f"slot_{slot_key}",
        )
=======
    scheduler = BackgroundScheduler(timezone=_KST)
    scheduler.add_job(_refresh_indicators, "date", run_date=datetime.now(_KST), kwargs={"force": True})
    scheduler.add_job(_refresh_indicators, CronTrigger(minute="0,30", timezone=_KST), max_instances=1, coalesce=True)
    if get_settings().heatmap_enabled:
        # 저장된 스냅샷을 먼저 복원. 수천 종목 초기 수집 동안에도 HTTP 서버는 응답한다.
        heatmap.initialize()
        scheduler.add_job(heatmap.refresh_all, "date", run_date=datetime.now(_KST), kwargs={"force": True})
        # 매분 체크하되 서비스가 10분 수집시점/휴장/마감 여부를 판단한다.
        # 30초 여유를 두어 15:30 마감 체결 반영 후 최종값을 저장한다.
        scheduler.add_job(heatmap.refresh_all, CronTrigger(minute="*", second=30, timezone=_KST), max_instances=1, coalesce=True)
    scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)
>>>>>>> 417a5403824a674ccf01b6c32189b97a377db9be


app = FastAPI(lifespan=lifespan)

# CORS - 허용할 프런트 주소와 메서드. 배포 주소가 생기면 allow_origins에 추가한다
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# 헬스 체크
@app.get("/")
def read_root():
    return {"message": "hello world"}


# 라우터 등록 - 도메인을 추가하면 여기에 include_router를 추가한다
app.include_router(timeline_router)
<<<<<<< HEAD
=======
app.include_router(calendar_router)
>>>>>>> 417a5403824a674ccf01b6c32189b97a377db9be
app.include_router(heatmap_router)
