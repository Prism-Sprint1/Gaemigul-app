# main.py

from contextlib import asynccontextmanager
from datetime import datetime
import logging
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.domain.calendar.routers.calendar import router as calendar_router
from backend.domain.calendar.services import calendar as calendar_service
from backend.domain.timeline.routers.timeline import router as timeline_router
from backend.domain.timeline.services import market_indicator_service

# minute="0,30" -> 매 시 0분/30분에 실행. 이 값을 바꾸면 갱신 주기가 바뀐다(예: "0,15,30,45"면 15분마다).
_KST = ZoneInfo("Asia/Seoul")
_logger = logging.getLogger(__name__)
_scheduler = BackgroundScheduler(timezone=_KST)


# calendar 도메인의 재수집 작업들(FOMC/FRED/DART)은 전부 같은 DB 엔진(core/database.py의
# 모듈 전역 async_session/engine, 프로세스 생명주기 동안 재사용되는 하나의 커넥션 풀)을
# 쓴다. 처음엔 다른 작업들처럼 BackgroundScheduler(스레드 풀)+asyncio.run()으로 만들었는데,
# 그러면 각 작업이 서로 다른 스레드에서 각자 새 이벤트 루프를 여는 데다, FastAPI 자체가
# 돌아가는 메인 이벤트 루프와도 다른 루프가 되어 커넥션 풀이 "attached to a different
# loop" 에러로 깨졌다(실제로 겪음 - 스레드 락으로 재수집 작업끼리는 겹치지 않게 했는데도
# 메인 루프의 실제 API 요청(`GET /calendar/events`)까지 500 에러가 났다). calendar 재수집
# 작업만 AsyncIOScheduler로 따로 둬서 FastAPI와 완전히 같은 이벤트 루프 안에서 코루틴으로
# 돌게 하면, 커넥션 풀이 항상 하나의 루프에만 묶여서 이 문제 자체가 생기지 않는다(락도
# 필요 없어짐 - 같은 루프 안에서는 await 지점에서만 다른 작업으로 넘어가므로 안전).
async def _refresh_fomc() -> None:
    try:
        await calendar_service.ingest_fomc_year(datetime.now(_KST).year)
    except Exception:
        _logger.exception("FOMC 캘린더 갱신 실패: 마지막 수집값을 유지합니다.")


# FRED 경제지표(CPI/PPI/GDP/PAYEMS/UNRATE/PCE)도 FOMC와 같은 문제를 겪었다 - 재수집
# 스케줄러가 하나도 없어서, BLS/BEA가 발표 이후 수치를 수정(revision)해도 예전에 한 번
# 수집한 옛날 값이 DB에 그대로 남아있었다(2026-09-17 실제로 PAYEMS 8월 값에서 발견 -
# 최신 고용 수치가 감소로 보였는데 실제로는 증가였고, 원인은 재수집 누락이었다). 이제
# ingest_year_from_fred도 upsert라 반복 실행해도 안전하니 FOMC와 같은 방식으로 주기
# 재수집한다. 지표 하나가 실패해도(예: FRED 순간 타임아웃) 나머지는 계속 진행한다.
_FRED_INDICATORS = ("CPI", "PPI", "GDP", "PAYEMS", "UNRATE", "PCE")


async def _refresh_fred_indicators() -> None:
    year = datetime.now(_KST).year
    for indicator in _FRED_INDICATORS:
        try:
            await calendar_service.ingest_year_from_fred(indicator, year)
        except Exception:
            _logger.exception("FRED %s 갱신 실패: 마지막 수집값을 유지합니다.", indicator)


# DART 잠정실적도 구조적으로는 FRED와 같은 위험(재수집 안 되면 나중에 나온 정정을 못 따라감)을
# 안고 있다 - 2026-09-17에 21건을 실제로 재조회해서 대조해봤을 땐 전부 저장값과 일치해서
# 지금 당장 틀린 값은 없었지만, "지금 문제없음"이 "앞으로도 문제없음"을 보장하진 않는다.
# corp_code는 scripts/test_dart_earnings.py의 COMPANIES와 동일(추측 아니고 dart_client.
# get_corp_codes()+find_corp_by_stock_code()로 실제 조회해서 확인한 값).
_DART_MAJOR_COMPANIES = (
    {"corp_code": "00126380", "corp_name": "삼성전자", "stock_code": "005930"},
    {"corp_code": "00164779", "corp_name": "SK하이닉스", "stock_code": "000660"},
    {"corp_code": "00164742", "corp_name": "현대차", "stock_code": "005380"},
)


async def _refresh_dart_earnings() -> None:
    today = datetime.now(_KST)
    start_date = f"{today.year - 1}0101"
    end_date = today.strftime("%Y%m%d")
    for company in _DART_MAJOR_COMPANIES:
        try:
            await calendar_service.ingest_preliminary_earnings_from_dart(
                company["corp_code"], company["stock_code"], company["corp_name"], start_date, end_date
            )
        except Exception:
            _logger.exception("DART %s 실적 갱신 실패: 마지막 수집값을 유지합니다.", company["corp_name"])


# 생명주기 이벤트
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 장이 닫혀있어도 서버가 켜질 땐 무조건 한 번 캐시를 채움
    market_indicator_service.refresh_all(force=True)
    _scheduler.add_job(market_indicator_service.refresh_all, CronTrigger(minute="0,30", timezone=_KST))
    _scheduler.start()

    # calendar 재수집 작업(FOMC/FRED/DART)만 별도의 AsyncIOScheduler로 돌린다 - 위
    # BackgroundScheduler는 스레드 풀에서 도는데, 이 작업들은 FastAPI와 같은 DB 커넥션
    # 풀을 쓰기 때문에 다른 스레드/이벤트 루프에서 건드리면 풀이 깨진다(주석 참고). 여기
    # lifespan 자체가 FastAPI의 메인 이벤트 루프 안에서 실행 중이므로, AsyncIOScheduler는
    # 자동으로 "지금 실행 중인" 이 루프를 그대로 쓴다.
    async_scheduler = AsyncIOScheduler(timezone=_KST)
    async_scheduler.add_job(_refresh_fomc, "date", run_date=datetime.now(_KST))
    async_scheduler.add_job(_refresh_fomc, CronTrigger(minute="0,30", timezone=_KST), max_instances=1, coalesce=True)
    async_scheduler.add_job(_refresh_fred_indicators, "date", run_date=datetime.now(_KST))
    # 월간 지표라 FOMC만큼 자주 볼 필요는 없다 - 6시간마다(하루 4번)면 발표 당일 갱신 지연도
    # 충분히 빨리 잡아내면서 FRED 호출 횟수도 아낄 수 있다.
    async_scheduler.add_job(_refresh_fred_indicators, CronTrigger(hour="*/6", minute=0, timezone=_KST), max_instances=1, coalesce=True)
    async_scheduler.add_job(_refresh_dart_earnings, "date", run_date=datetime.now(_KST))
    # DART 잠정실적은 분기당 1~2번, 그것도 특정 월에만 나온다 - FRED만큼 자주 볼 필요가
    # 없어서 하루 1번(자정 직후)이면 충분하다.
    async_scheduler.add_job(_refresh_dart_earnings, CronTrigger(hour=0, minute=10, timezone=_KST), max_instances=1, coalesce=True)
    async_scheduler.start()

    try:
        yield
    finally:
        _scheduler.shutdown(wait=False)
        async_scheduler.shutdown(wait=False)


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
app.include_router(calendar_router)
