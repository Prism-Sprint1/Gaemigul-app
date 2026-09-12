# main.py

import logging
from contextlib import asynccontextmanager
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import get_settings
from backend.core.logging_config import setup_logging
from backend.domain.timeline.routers.timeline import router as timeline_router
from backend.domain.timeline.services import market_indicator_service, timeline_service

# AsyncIOScheduler를 쓰는 이유
#   슬롯 수집 함수가 async def라서 그렇다. 예전에 쓰던 BackgroundScheduler는 별도 스레드에서 도는데,
#   스레드는 비동기 함수를 실행할 수 없다. 등록해두면 에러도 안 나고 아무 일도 안 일어난다.
#   AsyncIOScheduler는 FastAPI가 이미 돌리고 있는 이벤트 루프 위에서 돌아서 async 함수를 제대로 실행한다.
#   평범한 함수(지표 바 갱신)도 그대로 받아준다.
#
#   주의: 이벤트 루프가 있어야 도므로 서버를 띄웠을 때만 동작한다. 스크립트로 따로 실행하면 안 돈다.
# misfire_grace_time: 예약 시각에서 이만큼 늦어져도 실행한다 (초)
#   기본값이 1초라 서버가 잠깐 버벅이기만 해도 그 슬롯이 통째로 날아간다.
#   반대로 너무 길게 잡으면 안 된다. 맥이 잠들었다 몇 시간 뒤에 깨어났을 때 07:30 슬롯이
#   09시에 뒤늦게 실행되면, 그때 환율이 "07:30 가격"으로 저장돼 장중 변화가 틀린 값이 된다.
#   없는 것보다 틀린 게 나쁘므로 짧게 잡는다
logger = logging.getLogger(__name__)

_scheduler = AsyncIOScheduler(timezone=ZoneInfo("Asia/Seoul"), job_defaults={"misfire_grace_time": 10})


# 생명주기 이벤트
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 로그 설정을 가장 먼저 한다. 아래 작업 등록에서 나오는 경고도 파일에 남아야 한다
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


# 지표 바 갱신 예약 (매 시 0분/10분/20분/30분/40분/50분)
# minute 값을 바꾸면 갱신 주기가 바뀐다 (예: "0,30"이면 30분마다)
# 장이 닫혀있어도 서버가 켜질 땐 무조건 한 번 캐시를 채운다
# KIS 키가 없으면 지표 바만 꺼두고 앱은 정상 기동한다 (다른 도메인 작업을 막지 않기 위함)
def _register_indicator_job() -> None:
    try:
        market_indicator_service.refresh_all(force=True)
    except Exception as error:
        # RuntimeError(키 없음)뿐 아니라 KIS 장애·타임아웃(httpx 예외)도 여기서 막는다.
        # 예외가 lifespan 밖으로 나가면 앱이 통째로 기동 실패한다. 지표 바 하나 때문에
        # API 서버 전체가 안 뜨는 건 과하므로, 지표 바만 끄고 앱은 띄운다
        logger.warning("지표 바 비활성화 - %s: %s", type(error).__name__, error)
        return

    _scheduler.add_job(market_indicator_service.refresh_all, CronTrigger(minute="0,10,20,30,40,50"), id="indicator_bar")


# 타임라인 슬롯 수집 예약 (하루 8회)
# 시각은 timeline_service.SLOT_COLLECT_TIMES에 있다 - 바꾸려면 그 표를 고칠 것
# 휴장일 판단은 각 작업 안에서 한다(주말·공휴일이면 아무것도 하지 않는다)
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


# FastAPI 인스턴스 생성
app = FastAPI(lifespan=lifespan)

# CORS 및 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # 프론트 로컬 개발 서버 주소만 허용
    allow_methods=["GET", "POST"],  # POST /timeline/collect/{slot_key} 수동 수집용
    allow_headers=["*"],
)


# 기본 헬스 체크 엔드 포인트
@app.get("/")
def read_root():
    return {"message": "hello world"}


# 라우터 등록
app.include_router(timeline_router)
