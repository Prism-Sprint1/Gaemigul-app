"""FastAPI 앱 진입점과 백그라운드 시세 수집 작업."""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import get_settings
from backend.domain.heatmap.routers.heatmap import router as heatmap_router
from backend.domain.heatmap.services import heatmap
from backend.domain.timeline.routers.timeline import router as timeline_router
from backend.domain.timeline.services import market_indicator_service

_KST = ZoneInfo("Asia/Seoul")
_logger = logging.getLogger(__name__)


def _refresh_indicators(*, force: bool = False) -> None:
    try:
        market_indicator_service.refresh_all(force=force)
    except Exception:
        _logger.exception("시장 지표 갱신 실패: 마지막 수집값을 유지합니다.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler(timezone=_KST)
    scheduler.add_job(_refresh_indicators, "date", run_date=datetime.now(_KST), kwargs={"force": True})
    scheduler.add_job(
        _refresh_indicators,
        CronTrigger(minute="0,30", timezone=_KST),
        max_instances=1,
        coalesce=True,
    )
    if get_settings().heatmap_enabled:
        heatmap.initialize()
        scheduler.add_job(heatmap.refresh_all, "date", run_date=datetime.now(_KST), kwargs={"force": True})
        scheduler.add_job(
            heatmap.refresh_all,
            CronTrigger(minute="*", second=30, timezone=_KST),
            max_instances=1,
            coalesce=True,
        )
    scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)


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
app.include_router(heatmap_router)
