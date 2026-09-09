# import fastapi
# from ..schemas.calendar import CalendarEvent
# from ..services.calendar import get_calendar_events

# router = fastapi.APIRouter(
#     prefix="/calendar",
#     tags=["Calendar"],
# )


# @router.get("/events", response_model=list[CalendarEvent])
# def get_events():
#     return get_calendar_events()

# API 라우터 설정
# from fastapi import APIRouter

# from ..services.calendar import get_us_cpi


# router = APIRouter(
#     prefix="/calendar",
#     tags=["Calendar"],
# )


# @router.get("/events")
# async def get_events():
#     return await get_us_cpi()

# 3--------------------------------------------------
# FastAPI에서 API Router를 만들기 위한 클래스입니다.
# --------------------------------------------------
from fastapi import APIRouter


# --------------------------------------------------
# Calendar Service에서 미국 CPI 데이터를 가져옵니다.
# ★★★ 중요 ★★★
# get_us_cpi는 schemas가 아니라 services에 있습니다.
# --------------------------------------------------
from ..services.calendar import get_us_cpi


# ==================================================
# Calendar Router 생성
# ==================================================

router = APIRouter(

    # 모든 API 주소 앞에 /calendar를 붙입니다.
    #
    # 예:
    # /events
    # ↓
    # /calendar/events
    prefix="/calendar",

    # Swagger 문서에서 Calendar 그룹으로 표시됩니다.
    tags=["Calendar"],
)


# ==================================================
# 미국 CPI Calendar API
# ==================================================

@router.get("/events")
async def get_events():
    """
    Calendar 화면에서 사용할 미국 CPI 데이터를 반환합니다.
    """

    # Calendar Service의 get_us_cpi()를 호출합니다.
    #
    # async 함수이므로 await를 사용합니다.
    return await get_us_cpi()