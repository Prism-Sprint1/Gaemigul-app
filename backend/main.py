# main.py

from contextlib import asynccontextmanager
from datetime import datetime
import logging
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


# 생명주기 이벤트
@asynccontextmanager
async def lifespan(app: FastAPI):
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


# FastAPI 인스턴스 생성
app = FastAPI(lifespan=lifespan)

# CORS 및 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # 프론트 로컬 개발 서버 주소만 허용
    allow_methods=["GET"],
    allow_headers=["*"],
)


# 기본 헬스 체크 엔드 포인트
@app.get("/")
def read_root():
    return {"message": "hello world"}


# 라우터 등록
app.include_router(timeline_router)
<<<<<<< HEAD
app.include_router(calendar_router)
=======
app.include_router(heatmap_router)
>>>>>>> f40daca3888a40bb2757d936b7763fa0078f6d32
