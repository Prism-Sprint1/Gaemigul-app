# main.py
# FastAPI 인스턴스 생성
# CORS 및 미들웨어 설정
# 생명주기 이벤트
# 기본 헬스 체크 엔드 포인트
# 라우터 등록

from contextlib import asynccontextmanager
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.domain.timeline.routers.timeline import router as timeline_router
from backend.domain.timeline.services import market_indicator_service

# minute="0,30" -> 매 시 0분/30분에 실행. 이 값을 바꾸면 갱신 주기가 바뀐다(예: "0,15,30,45"면 15분마다).
_scheduler = BackgroundScheduler(timezone=ZoneInfo("Asia/Seoul"))


# 생명주기 이벤트
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 장이 닫혀있어도 서버가 켜질 땐 무조건 한 번 캐시를 채움
    market_indicator_service.refresh_all(force=True)
    _scheduler.add_job(market_indicator_service.refresh_all, CronTrigger(minute="0,30"))
    _scheduler.start()
    yield
    _scheduler.shutdown()


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
