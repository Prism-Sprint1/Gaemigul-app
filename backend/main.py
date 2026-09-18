# main.py
# FastAPI 앱 진입점. 로그 설정, 스케줄러(지표 바·market 데이터·슬롯·보고서), CORS, 라우터 등록.

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import get_settings
from backend.core.logging_config import setup_logging
from backend.domain.calendar.routers.calendar import router as calendar_router
from backend.domain.heatmap.routers.heatmap import router as heatmap_router
from backend.domain.heatmap.services import heatmap
from backend.domain.market.routers.market import router as market_router
from backend.domain.market.services import exchange_rate_service, investor_flow_service, sentiment_service, trading_value_service, vix_service
from backend.domain.timeline.routers.timeline import router as timeline_router
from backend.domain.timeline.services import market_indicator_service, report_service, timeline_service

logger = logging.getLogger(__name__)
_KST = ZoneInfo("Asia/Seoul")

# 예약 작업 스케줄러 (한국 시간 기준)
# AsyncIOScheduler는 서버의 이벤트 루프에서 돌아 async 함수를 실행할 수 있다. 서버가 떠 있을 때만 동작한다
# misfire_grace_time: 예약 시각보다 이 초만큼 늦어도 실행한다. 늘리면 맥이 잠들었다 깬 뒤에도
#   지난 슬롯이 실행되는데, 그러면 그 시각이 아닌 값이 저장되므로 짧게 둔다
_scheduler: AsyncIOScheduler | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _scheduler
    # 로그 설정을 가장 먼저 한다 (작업 등록 중 경고도 파일에 남도록)
    setup_logging()

    # async 작업은 이벤트 루프에서, 동기 수집은 executor에서 실행한다.
    # lifespan마다 새로 만들어 이전 실행의 닫힌 이벤트 루프를 재사용하지 않는다.
    _scheduler = AsyncIOScheduler(
        timezone=_KST,
        job_defaults={"misfire_grace_time": 10, "max_instances": 1, "coalesce": True},
    )
    heatmap.initialize()  # 외부 호출 없이 저장된 캐시만 복원한다.
    settings = get_settings()
    if settings.kis_app_key and settings.kis_app_secret:
        _register_indicator_job()
        _register_vix_job()
        _register_sentiment_job()
        _register_exchange_rate_job()
        _register_trading_value_job()
        _register_slot_jobs()
        _register_report_job()
        _register_heatmap_job()
    else:
        logger.warning("KIS 키가 없어 시세 수집을 시작하지 않습니다. 저장된 데이터와 API는 사용할 수 있습니다.")

    jobs = _scheduler.get_jobs()
    if jobs:
        _scheduler.start()
        logger.info("스케줄러 시작 - 작업 %d개 (%s)", len(jobs), ", ".join(job.id for job in jobs))
    else:
        logger.warning("등록된 예약 작업이 없습니다. .env의 KIS 키와 DATABASE_URL을 확인해주세요.")

    try:
        yield
    finally:
        if _scheduler.running:
            _scheduler.shutdown(wait=False)
            logger.info("스케줄러 종료")


# 지표 바 갱신 작업 등록 (10분마다). minute 값을 바꾸면 주기가 바뀐다 (예: "0,30"이면 30분마다)
# 초기 수집도 스케줄러에서 실행해 KIS/DB 응답을 기다리며 서버 시작을 막지 않는다.
# 첫 수집에 실패해도 예약 작업은 남아 다음 주기에 재시도한다.
def _refresh_indicator_bar() -> None:
    market_indicator_service.refresh_all(force=not bool(market_indicator_service.get_cache_snapshot()))


def _register_indicator_job() -> None:
    _scheduler.add_job(
        _refresh_indicator_bar,
        CronTrigger(minute="0,10,20,30,40,50", timezone=_KST),
        id="indicator_bar",
        next_run_time=datetime.now(_KST),
    )


# 메인 페이지 VIX 갱신 작업 등록 (24시간, 매시 00분·30분).
# 서버 시작 시 한 번 채우고 실패해도 예약 작업은 등록해 다음 00·30분에 다시 시도한다. KIS 호출은 kis_client 토큰 캐시를 그대로 쓴다.
def _register_vix_job() -> None:
    _scheduler.add_job(
        vix_service.refresh,
        CronTrigger(minute="0,30", timezone=_KST),
        id="market_vix",
        next_run_time=datetime.now(_KST),
        max_instances=1,
        coalesce=True,
    )


# 투자자 수급과 개미굴 시장심리지수는 같은 KIS 수급 원본을 공유한다.
# 서버 시작 시 한 번, 평일 국내장 09:00~15:30에 30분마다 갱신한다.
def _refresh_market_session() -> None:
    investor_raw = None
    try:
        investor_raw = investor_flow_service.refresh()
    except Exception as error:
        logger.warning("투자자 수급 갱신 실패 - %s: %s", type(error).__name__, error)

    try:
        sentiment_service.refresh(investor_raw)
    except Exception as error:
        logger.warning("개미굴 시장심리지수 갱신 실패 - %s: %s", type(error).__name__, error)


def _register_sentiment_job() -> None:
    _scheduler.add_job(
        _refresh_market_session,
        CronTrigger(day_of_week="mon-fri", hour="9-15", minute="0,30", timezone=_KST),
        id="market_session",
        next_run_time=datetime.now(_KST),
        max_instances=1,
        coalesce=True,
    )


# 원/달러 환율은 24시간 매시 00분·30분에 실제값을 DB에 적재하고 세 기간 캐시를 갱신한다.
# 초기 실행은 스케줄러 시작 직후 수행해 서버 시작 자체를 막지 않는다.
def _register_exchange_rate_job() -> None:
    if not get_settings().database_url:
        logger.warning("원/달러 환율 차트 비활성화 - DATABASE_URL이 .env에 없습니다.")
        return

    _scheduler.add_job(
        exchange_rate_service.refresh,
        CronTrigger(minute="0,30", timezone=_KST),
        id="market_exchange_rate",
        max_instances=1,
        coalesce=True,
        next_run_time=datetime.now(_KST),
    )


# 시간대별 거래대금은 서버 시작 시 최근 완성 거래일을 읽고, 평일 15:34에 오늘 완성본으로 교체한다.
# 타임라인 수집과 같은 분에 실행하되 KIS 호출 집중을 피하려고 거래대금은 30초 뒤에 시작한다.
def _register_trading_value_job() -> None:
    _scheduler.add_job(
        trading_value_service.refresh,
        CronTrigger(day_of_week="mon-fri", hour=15, minute=34, second=30, timezone=_KST),
        id="market_trading_value",
        next_run_time=datetime.now(_KST),
        max_instances=1,
        coalesce=True,
    )


# 슬롯 수집 작업 등록 (하루 8회). 시각은 timeline_service.SLOT_COLLECT_TIMES에서 바꾼다
# DATABASE_URL이 없으면 등록하지 않는다. 휴장일 판단은 작업 안에서 한다
def _register_slot_jobs() -> None:
    if not get_settings().database_url:
        logger.warning("타임라인 슬롯 수집 비활성화 - DATABASE_URL이 .env에 없습니다.")
        return

    for slot_key, (hour, minute) in timeline_service.SLOT_COLLECT_TIMES.items():
        _scheduler.add_job(
            timeline_service.run_scheduled_collect,
            CronTrigger(hour=hour, minute=minute, timezone=_KST),
            args=[slot_key],
            id=f"slot_{slot_key}",
        )


# 일간·주간 보고서는 20:00 슬롯과 분리해 20:05에 만든다.
# KIS의 투자자 수급·업종 거래대금이 20:00 직후에도 정산되는 것을 실데이터로 확인해 5분의 여유를 둔다.
def _register_report_job() -> None:
    if not get_settings().database_url:
        return

    _scheduler.add_job(
        report_service.run_scheduled_reports,
        CronTrigger(hour=20, minute=5, timezone=_KST),
        id="timeline_reports",
        max_instances=1,
        coalesce=True,
    )


def _register_heatmap_job() -> None:
    if not get_settings().heatmap_enabled:
        return
    # 시작 직후 및 매분 30초에 확인한다. 실제 시세 갱신은 서비스의 10분 구간 판정을 따른다.
    _scheduler.add_job(
        heatmap.refresh_all,
        CronTrigger(second=30, timezone=_KST),
        id="heatmap",
        next_run_time=datetime.now(_KST),
    )


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "hello world"}


app.include_router(timeline_router)
app.include_router(calendar_router)
app.include_router(heatmap_router)
app.include_router(market_router)
