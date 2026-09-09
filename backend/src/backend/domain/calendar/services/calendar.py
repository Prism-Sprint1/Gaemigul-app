# from typing import List  # noqa: UP035

# from ..schemas.calendar import CalendarEvent


# def get_calendar_events() -> List[CalendarEvent]:
#     return [
#         CalendarEvent(
#             date="2026-09-10",
#             time="21:30",
#             country="US",
#             category="경제",
#             title="미국 소비자물가지수(CPI)",
#             importance=5,
#             previous="2.7%",
#             forecast="2.8%",
#             actual=None,
#             status="SCHEDULED",
#         ),
#         CalendarEvent(
#             date="2026-09-11",
#             time="21:30",
#             country="US",
#             category="경제",
#             title="미국 생산자물가지수(PPI)",
#             importance=4,
#             previous="3.1%",
#             forecast="3.0%",
#             actual=None,
#             status="SCHEDULED",
#         ),
#         CalendarEvent(
#             date="2026-09-16",
#             time="03:00",
#             country="US",
#             category="금리",
#             title="FOMC 기준금리 결정",
#             importance=5,
#             previous="4.50%",
#             forecast="4.50%",
#             actual=None,
#             status="SCHEDULED",
#         ),
#     ]

# API 호출을 위한 서비스
# import os
# from typing import Any

# import httpx
# from dotenv import load_dotenv

# load_dotenv()

# FRED_API_URL = "https://api.stlouisfed.org/fred"


# def get_fred_api_key() -> str:
#     api_key = os.getenv("FRED_API_KEY")

#     if not api_key:
#         raise RuntimeError(
#             "FRED_API_KEY가 .env에 설정되어 있지 않습니다."
#         )

#     return api_key


# async def get_fred_series_observations(
#     series_id: str,
#     limit: int = 5,
# ) -> list[dict[str, Any]]:

#     params = {
#         "api_key": get_fred_api_key(),
#         "file_type": "json",
#         "series_id": series_id,
#         "limit": limit,
#         "sort_order": "desc",
#     }

#     async with httpx.AsyncClient(timeout=10.0) as client:
#         response = await client.get(
#             f"{FRED_API_URL}/series/observations",
#             params=params,
#         )

#     response.raise_for_status()

#     data = response.json()

#     return data.get("observations", [])


# async def get_us_cpi():
#     observations = await get_fred_series_observations(
#         series_id="CPIAUCSL",
#         limit=5,
#     )

#     return observations


# # FRED의 CPI 실제 발표일 → Calendar
# # 3--------------------------------------------------
# # 운영체제 환경변수(.env)에 접근하기 위한 모듈입니다.
# # FRED_API_KEY를 가져올 때 사용합니다.
# # --------------------------------------------------
# import os

# # --------------------------------------------------
# # 여러 종류의 데이터를 다루기 위한 타입 힌트입니다.
# # Any는 문자열, 숫자, 딕셔너리 등 다양한 타입을 허용합니다.
# # --------------------------------------------------
# from typing import Any

# # --------------------------------------------------
# # FRED API 서버에 HTTP 요청을 보내기 위한 라이브러리입니다.
# # 비동기(async) 방식으로 API를 호출할 수 있습니다.
# # --------------------------------------------------
# import httpx

# # --------------------------------------------------
# # .env 파일에 저장된 환경변수를 읽어오기 위한 라이브러리입니다.
# # --------------------------------------------------
# from dotenv import load_dotenv

# # --------------------------------------------------
# # 프로젝트의 .env 파일에 있는 환경변수를 읽습니다.
# # 예:
# # FRED_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# # --------------------------------------------------
# load_dotenv()


# # --------------------------------------------------
# # FRED API의 기본 주소입니다.
# # 뒤에 /series/release 같은 API 경로를 붙여서 사용합니다.
# # --------------------------------------------------
# FRED_API_URL = "https://api.stlouisfed.org/fred"


# # ==================================================
# # FRED API Key 가져오기
# # ==================================================

# def get_fred_api_key() -> str:
#     """
#     .env 파일에 저장된 FRED API Key를 가져옵니다.
#     """

#     # 환경변수 FRED_API_KEY를 읽습니다.
#     api_key = os.getenv("FRED_API_KEY")

#     # API Key가 없으면 에러를 발생시킵니다.
#     # 잘못된 요청이 FRED로 전달되는 것을 방지합니다.
#     if not api_key:

#         # 개발자가 문제를 바로 알 수 있도록 에러 메시지를 보여줍니다.
#         raise RuntimeError(
#             "FRED_API_KEY가 .env에 설정되어 있지 않습니다."
#         )

#     # 정상적으로 가져온 API Key를 반환합니다.
#     return api_key


# # ==================================================
# # FRED API 공통 요청 함수
# # ==================================================

# async def fred_get(
#     endpoint: str,
#     params: dict[str, Any],
# ) -> dict[str, Any]:
#     """
#     FRED API에 GET 요청을 보내는 공통 함수입니다.

#     endpoint:
#         FRED API의 세부 주소입니다.

#     params:
#         FRED API에 전달할 검색 조건입니다.
#     """

#     # FRED API Key를 params에 추가합니다.
#     params["api_key"] = get_fred_api_key()

#     # FRED API가 JSON 형식으로 응답하도록 요청합니다.
#     params["file_type"] = "json"

#     # 비동기 HTTP 클라이언트를 생성합니다.
#     # timeout=10은 최대 10초까지 응답을 기다린다는 뜻입니다.
#     async with httpx.AsyncClient(timeout=10.0) as client:

#         # FRED API에 GET 요청을 보냅니다.
#         response = await client.get(

#             # 기본 주소와 세부 API 주소를 합칩니다.
#             # 예:
#             # https://api.stlouisfed.org/fred/series/release
#             f"{FRED_API_URL}/{endpoint}",

#             # FRED에 전달할 파라미터입니다.
#             params=params,
#         )

#     # HTTP 오류가 발생하면 예외를 발생시킵니다.
#     # 예: API Key 오류, 잘못된 요청 등
#     response.raise_for_status()

#     # FRED가 보내준 JSON 데이터를 파이썬 딕셔너리로 변환합니다.
#     return response.json()


# # ==================================================
# # 1. CPI가 어떤 Release에 속하는지 확인
# # ==================================================

# async def get_cpi_release():
#     """
#     CPI 시리즈(CPIAUCSL)가 어떤 FRED Release에 연결되어 있는지
#     조회합니다.
#     """

#     # FRED의 series/release API를 호출합니다.
#     data = await fred_get(

#         # FRED의 시리즈 Release 조회 API입니다.
#         "series/release",

#         # CPI 시리즈 ID를 전달합니다.
#         {
#             "series_id": "CPIAUCSL",
#         },
#     )

#     # API 응답에서 releases 목록을 가져옵니다.
#     releases = data.get("releases", [])

#     # Release 정보가 하나도 없으면 에러를 발생시킵니다.
#     if not releases:

#         # CPI Release를 찾을 수 없다는 메시지를 표시합니다.
#         raise RuntimeError(
#             "CPI Release 정보를 찾을 수 없습니다."
#         )

#     # 첫 번째 Release 정보를 반환합니다.
#     return releases[0]


# # ==================================================
# # 2. CPI 실제 발표일 조회
# # ==================================================

# async def get_cpi_release_dates():
#     """
#     CPI의 실제 발표 일정을 FRED에서 가져옵니다.
#     """

#     # 먼저 CPI가 속한 Release 정보를 가져옵니다.
#     release = await get_cpi_release()

#     # Release 정보에서 Release ID를 가져옵니다.
#     release_id = release["id"]

#     # FRED의 release/dates API를 호출합니다.
#     data = await fred_get(

#         # Release 발표일 조회 API입니다.
#         "release/dates",

#         {
#             # CPI Release의 ID를 전달합니다.
#             "release_id": release_id,

#             # 최대 20개의 발표일을 가져옵니다.
#             "limit": 20,

#             # 최신 날짜부터 정렬합니다.
#             "sort_order": "desc",

#             # 아직 데이터가 없는 미래 발표일도 포함합니다.
#             # Calendar의 '발표 예정'을 만들기 위해 중요합니다.
#             "include_release_dates_with_no_data": "true",
#         },
#     )

#     # API 응답에서 release_dates 목록을 가져옵니다.
#     return data.get("release_dates", [])


# # ==================================================
# # 3. CPI 실제 데이터 조회
# # ==================================================

# async def get_cpi_observations():
#     """
#     FRED에서 CPI 실제 관측값을 가져옵니다.
#     """

#     # FRED의 series/observations API를 호출합니다.
#     data = await fred_get(

#         # 실제 경제지표 값을 가져오는 API입니다.
#         "series/observations",

#         {
#             # CPI 시리즈 ID입니다.
#             "series_id": "CPIAUCSL",

#             # 최근 데이터 5개만 가져옵니다.
#             "limit": 5,

#             # 최신 데이터부터 가져옵니다.
#             "sort_order": "desc",
#         },
#     )

#     # observations 배열을 반환합니다.
#     return data.get("observations", [])


# # ==================================================
# # 4. Calendar 화면에서 사용할 CPI 이벤트 만들기
# # ==================================================

# async def get_us_cpi():
#     """
#     FRED에서 가져온 CPI 정보를
#     우리 서비스의 Calendar 데이터 형태로 변환합니다.
#     """

#     # CPI의 실제 관측값을 가져옵니다.
#     observations = await get_cpi_observations()

#     # CPI의 발표 일정 정보를 가져옵니다.
#     release_dates = await get_cpi_release_dates()

#     # 관측값 중 가장 최근 데이터를 가져옵니다.
#     # 데이터가 없으면 None이 됩니다.
#     latest_observation = (
#         observations[0]
#         if observations
#         else None
#     )

#     # 발표 일정 중 가장 최근 날짜를 가져옵니다.
#     # 발표 일정이 없으면 None이 됩니다.
#     latest_release_date = (
#         release_dates[0]["date"]
#         if release_dates
#         else None
#     )

#     # 처음에는 실제 CPI 값을 None으로 설정합니다.
#     actual = None

#     # 실제 관측값이 존재한다면
#     if latest_observation:

#         # FRED가 제공한 실제 값을 가져옵니다.
#         actual = latest_observation["value"]

#     # ------------------------------------------------
#     # Calendar 화면에 필요한 데이터를 하나의 딕셔너리로
#     # 만들어 반환합니다.
#     # ------------------------------------------------

#     return {

#         # CPI 발표 날짜입니다.
#         "date": latest_release_date,

#         # 미국 CPI 발표 시간입니다.
#         # 한국 시간 기준으로 일단 21:30을 사용합니다.
#         "time": "21:30",

#         # 국가 코드입니다.
#         # US = United States
#         "country": "US",

#         # Calendar의 분류입니다.
#         "category": "경제",

#         # Calendar에 표시할 이벤트 이름입니다.
#         "title": "미국 소비자물가지수(CPI)",

#         # 중요도입니다.
#         # 5 = 최고 중요도
#         # 화면에서는 ★★★★★로 표시할 수 있습니다.
#         "importance": 5,

#         # 이전 발표값입니다.
#         # 아직 정확한 YoY 변환을 하지 않았기 때문에
#         # 일단 None으로 둡니다.
#         "previous": None,

#         # 시장 예상값입니다.
#         # FRED 기본 API에는 시장 컨센서스가 없기 때문에
#         # 일단 None으로 둡니다.
#         "forecast": None,

#         # FRED에서 가져온 실제 CPI 지수입니다.
#         "actual": actual,

#         # 현재는 발표 예정 상태로 표시합니다.
#         "status": "SCHEDULED",
#     }

# #4 --------------------------------------------------
# # 환경변수를 읽기 위한 모듈입니다.
# # .env에 저장된 FRED_API_KEY를 가져올 때 사용합니다.
# # --------------------------------------------------
# import os

# # --------------------------------------------------
# # 날짜와 시간을 계산하기 위한 모듈입니다.
# # 오늘 날짜와 CPI 발표일을 비교할 때 사용합니다.
# # --------------------------------------------------
# from datetime import date

# # --------------------------------------------------
# # 다양한 데이터 타입을 표현하기 위한 타입 힌트입니다.
# # --------------------------------------------------
# from typing import Any

# # --------------------------------------------------
# # FRED API에 HTTP 요청을 보내기 위한 라이브러리입니다.
# # --------------------------------------------------
# import httpx

# # --------------------------------------------------
# # .env 파일의 환경변수를 읽기 위한 라이브러리입니다.
# # --------------------------------------------------
# from dotenv import load_dotenv

# # --------------------------------------------------
# # 프로젝트의 .env 파일을 읽습니다.
# #
# # .env 예:
# # FRED_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# # --------------------------------------------------
# load_dotenv()


# # --------------------------------------------------
# # FRED API의 기본 주소입니다.
# # --------------------------------------------------
# FRED_API_URL = "https://api.stlouisfed.org/fred"


# # ==================================================
# # FRED API Key 가져오기
# # ==================================================

# def get_fred_api_key() -> str:
#     """
#     .env에 저장된 FRED API Key를 가져옵니다.
#     """

#     # 환경변수에서 FRED API Key를 가져옵니다.
#     api_key = os.getenv("FRED_API_KEY")

#     # API Key가 없으면 프로그램을 중단하고 오류를 보여줍니다.
#     if not api_key:
#         raise RuntimeError(
#             "FRED_API_KEY가 .env에 설정되어 있지 않습니다."
#         )

#     # 정상적으로 가져온 API Key를 반환합니다.
#     return api_key


# # ==================================================
# # FRED API 공통 GET 요청
# # ==================================================

# async def fred_get(
#     endpoint: str,
#     params: dict[str, Any],
# ) -> dict[str, Any]:
#     """
#     FRED API에 GET 요청을 보내는 공통 함수입니다.
#     """

#     # FRED API Key를 요청 파라미터에 추가합니다.
#     params["api_key"] = get_fred_api_key()

#     # FRED에게 JSON 형식으로 응답해 달라고 요청합니다.
#     params["file_type"] = "json"

#     # 비동기 HTTP 클라이언트를 생성합니다.
#     async with httpx.AsyncClient(timeout=10.0) as client:

#         # FRED API에 GET 요청을 보냅니다.
#         response = await client.get(

#             # 기본 URL + API endpoint를 연결합니다.
#             #
#             # 예:
#             # https://api.stlouisfed.org/fred/series/release
#             f"{FRED_API_URL}/{endpoint}",

#             # API에 전달할 파라미터입니다.
#             params=params,
#         )

#     # HTTP 오류가 발생하면 예외를 발생시킵니다.
#     response.raise_for_status()

#     # FRED의 JSON 응답을 Python 딕셔너리로 변환합니다.
#     return response.json()

# # ==================================================
# # CPI Release 정보 가져오기
# # ==================================================
# async def get_cpi_release():
#     """
#     CPIAUCSL이 어떤 FRED Release에 속해 있는지 가져옵니다.
#     """

#     # FRED의 series/release API를 호출합니다.
#     data = await fred_get(
#         "series/release",

#         # CPI 시리즈 ID를 전달합니다.
#         {
#             "series_id": "CPIAUCSL",
#         },
#     )

#     # API 응답에서 Release 목록을 가져옵니다.
#     releases = data.get("releases", [])

#     # Release가 없다면 오류를 발생시킵니다.
#     if not releases:
#         raise RuntimeError(
#             "CPI Release 정보를 찾을 수 없습니다."
#         )

#     # 첫 번째 Release 정보를 반환합니다.
#     return releases[0]

# # ==================================================
# # CPI 발표일 가져오기
# # ==================================================

# async def get_cpi_release_dates():
#     """
#     FRED에서 CPI 발표일 목록을 가져옵니다.
#     """

#     # CPI의 Release 정보를 먼저 가져옵니다.
#     release = await get_cpi_release()

#     # Release 정보에서 ID를 가져옵니다.
#     release_id = release["id"]

#     # FRED Release 날짜 API를 호출합니다.
#     data = await fred_get(
#         "release/dates",

#         {
#             # CPI Release ID입니다.
#             "release_id": release_id,

#             # 최근 20개의 발표일을 가져옵니다.
#             "limit": 20,

#             # 최신 날짜부터 정렬합니다.
#             "sort_order": "desc",

#             # 아직 실제 데이터가 없는 미래 발표일도 가져옵니다.
#             "include_release_dates_with_no_data": "true",
#         },
#     )

#     # 발표일 목록만 반환합니다.
#     return data.get("release_dates", [])
# # ==================================================
# # CPI 발표일 가져오기
# # ==================================================

# async def get_cpi_release_dates():
#     """
#     FRED에서 CPI 발표일 목록을 가져옵니다.
#     """

#     # CPI의 Release 정보를 먼저 가져옵니다.
#     release = await get_cpi_release()

#     # Release 정보에서 ID를 가져옵니다.
#     release_id = release["id"]

#     # FRED Release 날짜 API를 호출합니다.
#     data = await fred_get(
#         "release/dates",

#         {
#             # CPI Release ID입니다.
#             "release_id": release_id,

#             # 최근 20개의 발표일을 가져옵니다.
#             "limit": 20,

#             # 최신 날짜부터 정렬합니다.
#             "sort_order": "desc",

#             # 아직 실제 데이터가 없는 미래 발표일도 가져옵니다.
#             "include_release_dates_with_no_data": "true",
#         },
#     )

#     # 발표일 목록만 반환합니다.
#     return data.get("release_dates", [])


# # ==================================================
# # CPI 실제 데이터 가져오기
# # ==================================================

# async def get_cpi_observations():
#     """
#     FRED에서 CPI 실제 관측값을 가져옵니다.
#     """

#     # FRED의 observations API를 호출합니다.
#     data = await fred_get(
#         "series/observations",

#         {
#             # CPI 시리즈 ID입니다.
#             "series_id": "CPIAUCSL",

#             # 최근 5개의 데이터를 가져옵니다.
#             "limit": 5,

#             # 최신 데이터부터 정렬합니다.
#             "sort_order": "desc",
#         },
#     )

#     # observations 배열만 반환합니다.
#     return data.get("observations", [])


# # ==================================================
# # 발표일 기준 상태 결정
# # ==================================================
# def get_event_status(
#     release_date: str,
#     actual: str | None,
# ) -> str:
#     """
#     CPI 이벤트의 상태를 결정합니다.

#     발표 전:
#         SCHEDULED

#     발표 후:
#         RELEASED
#     """

#     # 문자열 형태의 발표일을 날짜 객체로 변환합니다.
#     release_day = date.fromisoformat(release_date)

#     # 오늘 날짜를 가져옵니다.
#     today = date.today()

#     # ------------------------------------------------
#     # 아직 발표일이 오지 않았다면
#     # ------------------------------------------------
#     if today < release_day:

#         # 발표 예정 상태를 반환합니다.
#         return "SCHEDULED"

#     # ------------------------------------------------
#     # 발표일이 지났고 실제 데이터가 있다면
#     # ------------------------------------------------
#     if actual is not None:

#         # 발표 완료 상태를 반환합니다.
#         return "RELEASED"
#     # ------------------------------------------------
#     # 발표일은 지났지만 실제 데이터가 없다면
#     # ------------------------------------------------
#     return "SCHEDULED"
# # ==================================================
# # Calendar용 미국 CPI 이벤트 생성
# # ==================================================

# async def get_us_cpi():
#     """
#     FRED의 CPI 데이터를 CalendarEvent 형태로 변환합니다.
#     """

#     # CPI 발표일 목록을 가져옵니다.
#     release_dates = await get_cpi_release_dates()

#     # CPI 실제 관측값을 가져옵니다.
#     observations = await get_cpi_observations()

#     # ------------------------------------------------
#     # 발표일이 없는 경우
#     # ------------------------------------------------
#     if not release_dates:

#         # Calendar에서 사용할 수 있도록 오류를 발생시킵니다.
#         raise RuntimeError(
#             "CPI 발표일 정보를 가져오지 못했습니다."
#         )

#     # 가장 최근 발표일을 가져옵니다.
#     latest_release_date = release_dates[0]["date"]

#     # ------------------------------------------------
#     # 가장 최근 실제 CPI 데이터를 가져옵니다.
#     # ------------------------------------------------

#     latest_observation = (
#         observations[0]
#         if observations
#         else None
#     )

#     # 실제 CPI 값은 처음에는 None으로 설정합니다.
#     actual = None

#     # 실제 관측값이 있다면
#     if latest_observation:

#         # FRED가 제공하는 실제 CPI 지수값을 가져옵니다.
#         actual = latest_observation["value"]

#     # ------------------------------------------------
#     # 발표일과 실제값을 기준으로 상태를 결정합니다.
#     # ------------------------------------------------

#     status = get_event_status(
#         release_date=latest_release_date,
#         actual=actual,
#     )

#     # ------------------------------------------------
#     # Calendar 화면에서 사용할 데이터 생성
#     # ------------------------------------------------

#     return {

#         # CPI 발표일입니다.
#         "date": latest_release_date,

#         # 미국 CPI 발표 시간입니다.
#         # 한국 화면에서 우선 21:30으로 표시합니다.
#         "time": "21:30",

#         # 미국을 의미합니다.
#         "country": "US",

#         # 경제 이벤트 카테고리입니다.
#         "category": "경제",

#         # Calendar에 표시할 이벤트 이름입니다.
#         "title": "미국 소비자물가지수(CPI)",

#         # 중요도 5점입니다.
#         # 프론트엔드에서 ★★★★★로 표시할 수 있습니다.
#         "importance": 5,

#         # 이전 값입니다.
#         # 다음 단계에서 CPI YoY 계산을 연결합니다.
#         "previous": None,

#         # 시장 예상값입니다.
#         # FRED 기본 데이터에는 컨센서스가 없으므로
#         # 현재는 None으로 둡니다.
#         "forecast": None,

#         # FRED에서 가져온 실제 CPI 값입니다.
#         #
#         # 발표 전에는 실제 데이터가 없을 수 있고,
#         # 발표 후에는 실제 CPI 값이 들어갑니다.
#         "actual": actual,

#         # 발표일을 기준으로 자동 결정된 상태입니다.
#         #
#         # SCHEDULED
#         # 또는
#         # RELEASED
#         "status": status,
#     }

# --------------------------------------------------
# 운영체제 환경변수를 읽기 위한 모듈입니다.
# .env에 저장된 FRED_API_KEY를 가져올 때 사용합니다.
# --------------------------------------------------
import os


# --------------------------------------------------
# 날짜를 비교하기 위한 모듈입니다.
# 오늘 날짜와 CPI 발표 예정일을 비교할 때 사용합니다.
# --------------------------------------------------
from datetime import date


# --------------------------------------------------
# 다양한 데이터 타입을 표현하기 위한 타입 힌트입니다.
# --------------------------------------------------
from typing import Any


# --------------------------------------------------
# FRED API에 HTTP 요청을 보내기 위한 라이브러리입니다.
# --------------------------------------------------
import httpx


# --------------------------------------------------
# .env 파일의 환경변수를 읽기 위한 라이브러리입니다.
# --------------------------------------------------
from dotenv import load_dotenv


# --------------------------------------------------
# .env 파일을 읽습니다.
#
# .env에 다음과 같이 FRED API Key가 있어야 합니다.
#
# FRED_API_KEY=발급받은키
# --------------------------------------------------
load_dotenv()


# --------------------------------------------------
# FRED API의 기본 주소입니다.
# --------------------------------------------------
FRED_API_URL = "https://api.stlouisfed.org/fred"


# ==================================================
# FRED API Key 가져오기
# ==================================================

def get_fred_api_key() -> str:
    """
    .env에 저장된 FRED API Key를 가져옵니다.
    """

    # 환경변수에서 FRED API Key를 가져옵니다.
    api_key = os.getenv("FRED_API_KEY")

    # API Key가 없다면 오류를 발생시킵니다.
    if not api_key:
        raise RuntimeError(
            "FRED_API_KEY가 .env에 설정되어 있지 않습니다."
        )

    # 정상적으로 가져온 API Key를 반환합니다.
    return api_key


# ==================================================
# FRED API 공통 GET 요청
# ==================================================

async def fred_get(
    endpoint: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """
    FRED API에 GET 요청을 보내는 공통 함수입니다.
    """

    # FRED API Key를 요청 파라미터에 추가합니다.
    params["api_key"] = get_fred_api_key()

    # FRED에게 JSON 형식으로 응답하도록 요청합니다.
    params["file_type"] = "json"

    # 비동기 HTTP 클라이언트를 생성합니다.
    async with httpx.AsyncClient(timeout=10.0) as client:

        # FRED API에 GET 요청을 보냅니다.
        response = await client.get(

            # 기본 주소와 세부 API 주소를 연결합니다.
            f"{FRED_API_URL}/{endpoint}",

            # API에 전달할 파라미터입니다.
            params=params,
        )

    # HTTP 오류가 발생하면 예외를 발생시킵니다.
    response.raise_for_status()

    # FRED의 JSON 응답을 Python 딕셔너리로 변환합니다.
    return response.json()


# ==================================================
# CPI Release 정보 가져오기
# ==================================================

async def get_cpi_release():
    """
    CPIAUCSL이 어떤 FRED Release에 연결되어 있는지 확인합니다.
    """

    # FRED의 series/release API를 호출합니다.
    data = await fred_get(
        "series/release",

        # CPI 시리즈 ID를 전달합니다.
        {
            "series_id": "CPIAUCSL",
        },
    )

    # API 응답에서 Release 목록을 가져옵니다.
    releases = data.get("releases", [])

    # Release 정보가 없다면 오류를 발생시킵니다.
    if not releases:
        raise RuntimeError(
            "CPI Release 정보를 찾을 수 없습니다."
        )

    # 첫 번째 Release 정보를 반환합니다.
    return releases[0]


# ==================================================
# CPI 발표일 전체 가져오기
# ==================================================

async def get_cpi_release_dates():
    """
    FRED에서 CPI 발표일 목록을 가져옵니다.
    """

    # CPI Release 정보를 가져옵니다.
    release = await get_cpi_release()

    # Release ID를 가져옵니다.
    release_id = release["id"]

    # FRED의 Release 날짜 API를 호출합니다.
    data = await fred_get(
        "release/dates",

        {
            # CPI Release ID입니다.
            "release_id": release_id,

            # 최근 20개의 발표일을 가져옵니다.
            "limit": 20,

            # 최신 날짜부터 정렬합니다.
            "sort_order": "desc",

            # 미래 발표일도 포함합니다.
            #
            # Calendar에서 '발표 예정' 이벤트를
            # 만들기 위해 중요합니다.
            "include_release_dates_with_no_data": "true",
        },
    )

    # 발표일 목록만 반환합니다.
    return data.get("release_dates", [])


# ==================================================
# 가장 가까운 미래 CPI 발표일 찾기
# ==================================================

def get_next_release_date(
    release_dates: list[dict[str, Any]],
) -> str:
    """
    FRED에서 가져온 발표일 중
    오늘과 같거나 오늘 이후의 가장 가까운 날짜를 찾습니다.
    """

    # 현재 날짜를 가져옵니다.
    today = date.today()

    # 미래 발표일을 저장할 리스트입니다.
    future_dates = []

    # FRED가 제공한 발표일을 하나씩 확인합니다.
    for item in release_dates:

        # FRED의 발표일을 문자열로 가져옵니다.
        release_date = item.get("date")

        # 날짜 정보가 없는 항목은 건너뜁니다.
        if not release_date:
            continue

        # 문자열을 Python date 객체로 변환합니다.
        release_day = date.fromisoformat(release_date)

        # 오늘과 같거나 미래인 날짜만 선택합니다.
        if release_day >= today:

            # 미래 발표일 목록에 추가합니다.
            future_dates.append(release_day)

    # 미래 발표일이 하나도 없다면 오류를 발생시킵니다.
    if not future_dates:
        raise RuntimeError(
            "가까운 미래 CPI 발표일을 찾을 수 없습니다."
        )

    # 가장 빠른 날짜를 선택합니다.
    next_release = min(future_dates)

    # Calendar에서 사용할 수 있도록 문자열로 변환합니다.
    return next_release.isoformat()


# ==================================================
# CPI 실제 관측값 가져오기
# ==================================================

async def get_cpi_observations():
    """
    FRED에서 CPI 실제 관측값을 가져옵니다.
    """

    # FRED의 series/observations API를 호출합니다.
    data = await fred_get(
        "series/observations",

        {
            # CPI 시리즈 ID입니다.
            "series_id": "CPIAUCSL",

            # 최근 5개의 CPI 데이터를 가져옵니다.
            "limit": 5,

            # 최신 데이터부터 정렬합니다.
            "sort_order": "desc",
        },
    )

    # observations 목록만 반환합니다.
    return data.get("observations", [])


# # 5==================================================
# # Calendar 이벤트 상태 결정
# # ==================================================

# def get_event_status(
#     release_date: str,
#     actual: str | None,
# ) -> str:
#     """
#     CPI 발표일과 실제 데이터 존재 여부를 기준으로
#     이벤트 상태를 결정합니다.

#     발표 전:
#         SCHEDULED

#     발표 후 + 실제값 존재:
#         RELEASED
#     """

#     # 발표일 문자열을 date 객체로 변환합니다.
#     release_day = date.fromisoformat(release_date)

#     # 오늘 날짜를 가져옵니다.
#     today = date.today()

#     # 아직 발표일이 오지 않았다면
#     if today < release_day:

#         # 발표 예정 상태를 반환합니다.
#         return "SCHEDULED"

#     # 발표일이 지났고 실제값이 있다면
#     if actual is not None:

#         # 발표 완료 상태를 반환합니다.
#         return "RELEASED"

#     # 발표일이 지났지만 실제값이 없다면
#     # 안전하게 발표 예정 상태로 유지합니다.
#     return "SCHEDULED"


# # ==================================================
# # 미국 CPI Calendar 이벤트 생성
# # ==================================================

# async def get_us_cpi():
#     """
#     FRED 데이터를 Calendar 화면에서 사용할 수 있는
#     미국 CPI 이벤트 데이터로 변환합니다.
#     """

#     # ------------------------------------------------
#     # 1. CPI 발표일 가져오기
#     # ------------------------------------------------

#     release_dates = await get_cpi_release_dates()

#     # 발표일이 없다면 오류를 발생시킵니다.
#     if not release_dates:
#         raise RuntimeError(
#             "CPI 발표일 정보를 가져오지 못했습니다."
#         )

#     # ------------------------------------------------
#     # 2. 가장 가까운 미래 발표일 찾기
#     # ------------------------------------------------

#     next_release_date = get_next_release_date(
#         release_dates
#     )

#     # ------------------------------------------------
#     # 3. CPI 실제 관측값 가져오기
#     # ------------------------------------------------

#     observations = await get_cpi_observations()

#     # 최근 관측값을 가져옵니다.
#     latest_observation = (
#         observations[0]
#         if observations
#         else None
#     )

#     # 실제값은 기본적으로 None입니다.
#     actual = None

#     # 관측값이 있다면
#     if latest_observation:

#         # FRED의 실제 CPI 지수값을 가져옵니다.
#         actual = latest_observation["value"]

#     # ------------------------------------------------
#     # 4. 발표일과 실제값을 이용해서 상태 결정
#     # ------------------------------------------------

#     status = get_event_status(
#         release_date=next_release_date,
#         actual=actual,
#     )

#     # ------------------------------------------------
#     # 5. Calendar 화면에 전달할 데이터 생성
#     # ------------------------------------------------

#     return {

#         # 가장 가까운 미래 CPI 발표일입니다.
#         "date": next_release_date,

#         # 미국 CPI 발표 시간입니다.
#         #
#         # 현재는 한국 시간 기준으로
#         # 임시로 21:30을 사용합니다.
#         "time": "21:30",

#         # 미국을 의미합니다.
#         "country": "US",

#         # 경제 이벤트입니다.
#         "category": "경제",

#         # Calendar에 표시할 이름입니다.
#         "title": "미국 소비자물가지수(CPI)",

#         # 중요도 최고 등급입니다.
#         #
#         # 프론트엔드에서:
#         # 5 → ★★★★★
#         # 로 표시할 수 있습니다.
#         "importance": 5,

#         # 이전 CPI 값입니다.
#         #
#         # 다음 단계에서 YoY 계산을 넣겠습니다.
#         "previous": None,

#         # 시장 예상값입니다.
#         #
#         # FRED에는 일반적인 시장 컨센서스가 없으므로
#         # 현재는 None으로 둡니다.
#         "forecast": None,

#         # FRED에서 가져온 실제 CPI 지수입니다.
#         "actual": actual,

#         # SCHEDULED 또는 RELEASED입니다.
#         "status": status,
#     }
# # 6--------------------------------------------------
# # 환경변수를 읽기 위한 모듈
# # --------------------------------------------------
# import os


# # --------------------------------------------------
# # 날짜를 다루기 위한 모듈
# # --------------------------------------------------
# from datetime import date


# # --------------------------------------------------
# # 다양한 데이터 타입을 표현하기 위한 타입
# # --------------------------------------------------
# from typing import Any


# # --------------------------------------------------
# # FRED API에 HTTP 요청을 보내기 위한 라이브러리
# # --------------------------------------------------
# import httpx


# # --------------------------------------------------
# # .env 파일을 읽기 위한 라이브러리
# # --------------------------------------------------
# from dotenv import load_dotenv


# # --------------------------------------------------
# # .env 파일의 환경변수를 불러옵니다.
# # --------------------------------------------------
# load_dotenv()


# # --------------------------------------------------
# # FRED API 기본 주소
# # --------------------------------------------------
# FRED_API_URL = "https://api.stlouisfed.org/fred"


# # ==================================================
# # FRED API KEY
# # ==================================================

# def get_fred_api_key() -> str:
#     """
#     .env에서 FRED API Key를 가져옵니다.
#     """

#     # 환경변수에서 API Key를 가져옵니다.
#     api_key = os.getenv("FRED_API_KEY")

#     # API Key가 없다면 오류를 발생시킵니다.
#     if not api_key:
#         raise RuntimeError(
#             "FRED_API_KEY가 .env에 설정되어 있지 않습니다."
#         )

#     # API Key 반환
#     return api_key


# # ==================================================
# # FRED 공통 GET 요청
# # ==================================================

# async def fred_get(
#     endpoint: str,
#     params: dict[str, Any],
# ) -> dict[str, Any]:
#     """
#     FRED API에 GET 요청을 보내는 공통 함수입니다.
#     """

#     # API Key를 요청 파라미터에 추가합니다.
#     params["api_key"] = get_fred_api_key()

#     # JSON 형식으로 응답받습니다.
#     params["file_type"] = "json"

#     # 비동기 HTTP 클라이언트를 생성합니다.
#     async with httpx.AsyncClient(timeout=10.0) as client:

#         # FRED API에 GET 요청을 보냅니다.
#         response = await client.get(
#             f"{FRED_API_URL}/{endpoint}",
#             params=params,
#         )

#     # HTTP 오류가 발생하면 예외를 발생시킵니다.
#     response.raise_for_status()

#     # JSON을 Python 딕셔너리로 변환합니다.
#     return response.json()


# # ==================================================
# # CPI Release 정보 가져오기
# # ==================================================

# async def get_cpi_release():
#     """
#     CPIAUCSL이 속해 있는 FRED Release 정보를 가져옵니다.
#     """

#     # series/release API 호출
#     data = await fred_get(
#         "series/release",
#         {
#             "series_id": "CPIAUCSL",
#         },
#     )

#     # Release 목록 가져오기
#     releases = data.get("releases", [])

#     # Release가 없다면 오류 발생
#     if not releases:
#         raise RuntimeError(
#             "CPI Release 정보를 찾을 수 없습니다."
#         )

#     # 첫 번째 Release 반환
#     return releases[0]


# # ==================================================
# # CPI 발표일 가져오기
# # ==================================================

# async def get_cpi_release_dates():
#     """
#     CPI의 발표일 목록을 가져옵니다.
#     """

#     # CPI Release 정보를 가져옵니다.
#     release = await get_cpi_release()

#     # Release ID를 가져옵니다.
#     release_id = release["id"]

#     # Release 날짜 API 호출
#     data = await fred_get(
#         "release/dates",
#         {
#             # CPI Release ID
#             "release_id": release_id,

#             # 최대 20개 날짜 조회
#             "limit": 20,

#             # 최신 날짜부터 정렬
#             "sort_order": "desc",

#             # 미래 발표일도 포함
#             "include_release_dates_with_no_data": "true",
#         },
#     )

#     # 발표일 목록 반환
#     return data.get("release_dates", [])


# # ==================================================
# # 가장 가까운 미래 발표일 찾기
# # ==================================================

# def get_next_release_date(
#     release_dates: list[dict[str, Any]],
# ) -> str:
#     """
#     오늘 이후 가장 가까운 CPI 발표일을 찾습니다.
#     """

#     # 오늘 날짜
#     today = date.today()

#     # 미래 발표일을 저장할 리스트
#     future_dates = []

#     # FRED 발표일을 하나씩 확인합니다.
#     for item in release_dates:

#         # 발표일 가져오기
#         release_date = item.get("date")

#         # 날짜가 없다면 건너뜁니다.
#         if not release_date:
#             continue

#         # 문자열을 날짜 객체로 변환합니다.
#         release_day = date.fromisoformat(
#             release_date
#         )

#         # 오늘과 같거나 미래인 날짜만 선택합니다.
#         if release_day >= today:

#             # 미래 날짜 목록에 추가합니다.
#             future_dates.append(release_day)

#     # 미래 날짜가 없다면 오류 발생
#     if not future_dates:
#         raise RuntimeError(
#             "가까운 미래 CPI 발표일을 찾을 수 없습니다."
#         )

#     # 가장 가까운 미래 날짜를 선택합니다.
#     next_release = min(future_dates)

#     # 문자열로 반환합니다.
#     return next_release.isoformat()


# # ==================================================
# # CPI 실제 데이터 가져오기
# # ==================================================

# async def get_cpi_observations():
#     """
#     CPI 실제 관측값을 가져옵니다.
#     """

#     # FRED observations API 호출
#     data = await fred_get(
#         "series/observations",
#         {
#             # CPI 시리즈
#             "series_id": "CPIAUCSL",

#             # 최근 데이터 5개
#             "limit": 5,

#             # 최신 데이터부터
#             "sort_order": "desc",
#         },
#     )

#     # observations 반환
#     return data.get("observations", [])


# # ==================================================
# # Calendar 상태 결정
# # ==================================================

# def get_event_status(
#     release_date: str,
# ) -> str:
#     """
#     CPI 발표일을 기준으로 이벤트 상태를 결정합니다.

#     발표 전:
#         SCHEDULED

#     발표일 당일 또는 이후:
#         RELEASED
#     """

#     # 발표일을 날짜 객체로 변환합니다.
#     release_day = date.fromisoformat(
#         release_date
#     )

#     # 오늘 날짜
#     today = date.today()

#     # 발표일이 아직 오지 않았다면
#     if today < release_day:

#         # 발표 예정
#         return "SCHEDULED"

#     # 발표일 당일 또는 발표일 이후
#     return "RELEASED"


# # ==================================================
# # CPI Calendar 이벤트 생성
# # ==================================================

# async def get_us_cpi():
#     """
#     FRED CPI 데이터를 Calendar 이벤트 형태로 변환합니다.
#     """

#     # ------------------------------------------------
#     # 1. CPI 발표일 가져오기
#     # ------------------------------------------------

#     release_dates = await get_cpi_release_dates()

#     # 발표일이 없다면 오류
#     if not release_dates:
#         raise RuntimeError(
#             "CPI 발표일 정보를 가져오지 못했습니다."
#         )

#     # ------------------------------------------------
#     # 2. 가장 가까운 미래 발표일 찾기
#     # ------------------------------------------------

#     next_release_date = get_next_release_date(
#         release_dates
#     )

#     # ------------------------------------------------
#     # 3. 발표일 기준 상태 결정
#     # ------------------------------------------------

#     status = get_event_status(
#         next_release_date
#     )

#     # ------------------------------------------------
#     # 4. 실제 CPI 데이터 가져오기
#     # ------------------------------------------------

#     observations = await get_cpi_observations()

#     # 실제 CPI 값
#     actual = None

#     # ------------------------------------------------
#     # 발표가 끝난 경우에만 Actual을 넣습니다.
#     # ------------------------------------------------

#     if status == "RELEASED" and observations:

#         # 가장 최근 CPI 실제값
#         actual = observations[0]["value"]

#     # ------------------------------------------------
#     # 5. Calendar 이벤트 반환
#     # ------------------------------------------------

#     return {

#         # 가장 가까운 CPI 발표일
#         "date": next_release_date,

#         # 현재는 한국 시간 기준 임시값
#         "time": "21:30",

#         # 미국
#         "country": "US",

#         # 경제 이벤트
#         "category": "경제",

#         # 이벤트 이름
#         "title": "미국 소비자물가지수(CPI)",

#         # 최고 중요도
#         "importance": 5,

#         # 이전 값
#         # 다음 단계에서 계산합니다.
#         "previous": None,

#         # 시장 예상값
#         # FRED 기본 API에는 없으므로 아직 None
#         "forecast": None,

#         # 발표 전에는 None
#         # 발표 후에는 Actual 값
#         "actual": actual,

#         # SCHEDULED 또는 RELEASED
#         "status": status,
#     }
#7--------------------------------------------------
# 환경변수를 읽기 위한 모듈
# --------------------------------------------------
import os

# --------------------------------------------------
# 날짜를 다루기 위한 모듈
# --------------------------------------------------
from datetime import date


# --------------------------------------------------
# 다양한 데이터 타입을 표현하기 위한 타입
# --------------------------------------------------
from typing import Any

# --------------------------------------------------
# FRED API에 HTTP 요청을 보내기 위한 라이브러리
# --------------------------------------------------
import httpx


# --------------------------------------------------
# .env 파일을 읽기 위한 라이브러리
# --------------------------------------------------
from dotenv import load_dotenv

# ============================================================
# 1. 환경변수(.env) 불러오기
# ============================================================
load_dotenv()



# ============================================================
# 2. FRED API 기본 주소
# ============================================================
FRED_API_URL = "https://api.stlouisfed.org/fred"




## ============================================================
# 3. FRED API Key 가져오기
# ============================================================

def get_fred_api_key() -> str:

    # .env에 저장해 둔 FRED_API_KEY를 가져옵니다.
    api_key = os.getenv("FRED_API_KEY")

    # API Key가 없으면 에러를 발생시킵니다.
    if not api_key:
        raise RuntimeError("FRED_API_KEY가 .env에 없습니다.")

    return api_key


# ============================================================
# 4. FRED API 공통 요청 함수
# ============================================================

async def fred_get(
    endpoint: str,
    params: dict[str, Any],
) -> dict[str, Any]:

    # FRED API Key를 가져옵니다.
    api_key = get_fred_api_key()

    # FRED API에서 공통적으로 사용하는 파라미터를 추가합니다.
    params = {
        **params,
        "api_key": api_key,
        "file_type": "json",
    }

    # FRED API에 HTTP GET 요청을 보냅니다.
    async with httpx.AsyncClient(timeout=10.0) as client:

        response = await client.get(
            f"{FRED_API_URL}/{endpoint}",
            params=params,
        )

        # HTTP 오류가 발생하면 예외를 발생시킵니다.
        response.raise_for_status()

        # Model과 연결쪽

        # JSON 데이터를 반환합니다.
        return response.json()


# ============================================================
# 5. CPI 발표 일정 가져오기
# ============================================================

async def get_cpi_release_dates() -> list[str]:

    # FRED의 CPI Release ID는 10입니다.
    release_id = 10

    # CPI 발표일 목록을 요청합니다.
    data = await fred_get(
        "release/dates",
        {
            "release_id": release_id,
            "limit": 20,
            "sort_order": "desc",

            # 아직 데이터가 나오지 않은 미래 발표일도 포함합니다.
            "include_release_dates_with_no_data": "true",
        },
    )

    # release_dates 안에 발표일 목록이 들어 있습니다.
    return [
        item["date"]
        for item in data.get("release_dates", [])
    ]


# ============================================================
# 6. 가장 가까운 미래 CPI 발표일 찾기
# ============================================================

def get_next_release_date(
    release_dates: list[str],
) -> str | None:

    # 오늘 날짜를 가져옵니다.
    today = date.today()

    # 오늘 이후의 발표일만 추립니다.
    future_dates = [
        release_date
        for release_date in release_dates
        if date.fromisoformat(release_date) >= today
    ]

    # 미래 발표일이 없으면 None을 반환합니다.
    if not future_dates:
        return None

    # 가장 가까운 발표일을 반환합니다.
    return min(future_dates)


# ============================================================
# 7. CPI 실제 데이터 가져오기
# ============================================================

async def get_cpi_observations() -> list[dict[str, Any]]:

    # CPIAUCSL은 미국 소비자물가지수(CPI) 원지수입니다.
    series_id = "CPIAUCSL"

    # 전년 대비 계산을 위해 최소 13개월 데이터를 가져옵니다.
    data = await fred_get(
        "series/observations",
        {
            "series_id": series_id,
            "limit": 13,
            "sort_order": "desc",
        },
    )

    return data.get("observations", [])


# ============================================================
# 8. CPI YoY 계산
# ============================================================

def calculate_cpi_yoy(
    observations: list[dict[str, Any]]
) -> float | None:

    # 데이터가 13개월보다 적으면 계산할 수 없습니다.
    if len(observations) < 13:
        return None

    try:

        # 가장 최근 CPI 지수
        current_value = float(
            observations[0]["value"]
        )

        # 12개월 전 CPI 지수
        previous_year_value = float(
            observations[12]["value"]
        )

        # 전년 대비 상승률 계산
        yoy = (
            (current_value / previous_year_value) - 1
        ) * 100

        # 소수점 둘째 자리까지 반환합니다.
        return round(yoy, 2)

    except (KeyError, ValueError, TypeError):

        # 데이터가 잘못된 경우 None을 반환합니다.
        return None


# ============================================================
# 9. CPI 데이터 조회
# ============================================================

async def get_us_cpi():

    # --------------------------------------------------------
    # ① CPI 발표일 가져오기
    # --------------------------------------------------------

    release_dates = await get_cpi_release_dates()

    # --------------------------------------------------------
    # ② 가장 가까운 미래 발표일 찾기
    # --------------------------------------------------------

    next_release_date = get_next_release_date(
        release_dates
    )

    # 발표일을 찾지 못한 경우
    if not next_release_date:

        return {
            "date": None,
            "time": None,
            "country": "US",
            "category": "경제",
            "title": "미국 소비자물가지수(CPI)",
            "importance": 5,
            "previous": None,
            "forecast": None,
            "actual": None,
            "status": "UNKNOWN",
        }

    # --------------------------------------------------------
    # ③ CPI 실제 데이터 가져오기
    # --------------------------------------------------------

    observations = await get_cpi_observations()

    # --------------------------------------------------------
    # ④ 최근 CPI YoY 계산
    # --------------------------------------------------------

    current_yoy = calculate_cpi_yoy(
        observations
    )

    # --------------------------------------------------------
    # ⑤ 이전 CPI YoY 계산
    #
    # 현재 CPI가 발표되기 전에는
    # 가장 최근 발표된 CPI를 Previous로 보여줍니다.
    # --------------------------------------------------------

    previous_yoy = None

    if len(observations) >= 14:

        try:

            current_index = float(
                observations[0]["value"]
            )

            previous_month_index = float(
                observations[1]["value"]
            )

            previous_year_index = float(
                observations[13]["value"]
            )

            previous_yoy = round(
                (
                    previous_month_index
                    / previous_year_index
                    - 1
                )
                * 100,
                2,
            )

        except (KeyError, ValueError, TypeError):

            previous_yoy = None

    # --------------------------------------------------------
    # ⑥ 현재 날짜
    # --------------------------------------------------------

    today = date.today()

    release_date = date.fromisoformat(
        next_release_date
    )

    # --------------------------------------------------------
    # ⑦ 발표 전 / 발표 후 상태 결정
    # --------------------------------------------------------

    if today < release_date:

        status = "SCHEDULED"

        actual = None

    else:

        status = "RELEASED"

        actual = current_yoy

    # --------------------------------------------------------
    # ⑧ Calendar Event 반환
    # --------------------------------------------------------

    return {

        # 발표일
        "date": next_release_date,

        # 현재는 임시로 21:30
        "time": "21:30",

        # 국가
        "country": "US",

        # 카테고리
        "category": "경제",

        # 이벤트명
        "title": "미국 소비자물가지수(CPI)",

        # 중요도
        "importance": 5,

        # 직전 CPI
        "previous": (
            f"{previous_yoy}%"
            if previous_yoy is not None
            else None
        ),

        # 전망치는 아직 외부 데이터가 없으므로 None
        "forecast": None,

        # 발표 전에는 None
        # 발표 후에는 실제 CPI
        "actual": (
            f"{actual}%"
            if actual is not None
            else None
        ),

        # 이벤트 상태
        "status": status,
    }