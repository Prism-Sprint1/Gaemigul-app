# fred_client.py
# FRED(미국 연방준비제도 경제 데이터) API 직접 호출
#
# core에 있는 이유: kis_client.py와 같은 팀 규칙 - 여러 도메인이 같이 쓸 수 있도록
# API 호출 코드는 도메인 안에 두지 않고 core에 모아서 전역으로 쓴다(2026-09-10).

from __future__ import annotations

import httpx

from backend.core.config import get_settings

_BASE_URL = "https://api.stlouisfed.org/fred"


def _get(path: str, **params: str | int) -> dict:
    settings = get_settings()
    response = httpx.get(
        f"{_BASE_URL}{path}",
        params={
            **params,
            "api_key": settings.fred_api_key,
            "file_type": "json",
        },
    )
    response.raise_for_status()
    return response.json()


# 시계열의 관측치를 조회. limit=2/sort_order="desc"(기본값)면 [최신값, 직전값] 순서로 온다.
# observation_start/end("YYYY-MM-DD")를 주면 그 기간의 관측치를 전부 가져올 수 있다 - 기간 밖의
# 미래 관측치는 FRED에 데이터 자체가 없어서 응답에 아예 안 나온다(임의 생성 위험 없음).
# value가 "."이면 해당 시점에 실제 값이 없다는 뜻 (FRED 자체 규칙)
def get_series_observations(
    series_id: str,
    *,
    limit: int = 2,
    sort_order: str = "desc",
    observation_start: str | None = None,
    observation_end: str | None = None,
) -> list[dict]:
    params: dict[str, str | int] = {
        "series_id": series_id,
        "sort_order": sort_order,
        "limit": limit,
    }
    if observation_start is not None:
        params["observation_start"] = observation_start
    if observation_end is not None:
        params["observation_end"] = observation_end

    body = _get("/series/observations", **params)
    return body["observations"]


# 이 시계열이 속한 release_id 조회 (release_id가 있어야 실제 발표일을 조회할 수 있다)
def get_series_release_id(series_id: str) -> int:
    body = _get("/series/release", series_id=series_id)
    return body["releases"][0]["id"]


# 해당 release의 실제 발표일(날짜만, 시각 없음)을 조회.
# include_release_dates_with_no_data=True를 줘야 "아직 데이터는 없지만 예정된" 미래 발표일까지
# 나온다 - 이게 없으면 이미 지나간 발표일만 나온다(FRED 자체 규칙, 실제 라이브 호출로 확인함).
def get_release_dates(
    release_id: int,
    *,
    limit: int = 1,
    sort_order: str = "desc",
    realtime_start: str | None = None,
    realtime_end: str | None = None,
    include_release_dates_with_no_data: bool = False,
) -> list[dict]:
    params: dict[str, str | int] = {
        "release_id": release_id,
        "sort_order": sort_order,
        "limit": limit,
    }
    if realtime_start is not None:
        params["realtime_start"] = realtime_start
    if realtime_end is not None:
        params["realtime_end"] = realtime_end
    if include_release_dates_with_no_data:
        params["include_release_dates_with_no_data"] = "true"

    body = _get("/release/dates", **params)
    return body["release_dates"]
