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


# 시계열의 관측치를 최신순으로 조회. limit=2면 [최신값, 직전값] 순서로 온다
# value가 "."이면 해당 시점에 실제 값이 없다는 뜻 (FRED 자체 규칙)
def get_series_observations(series_id: str, *, limit: int = 2) -> list[dict]:
    body = _get(
        "/series/observations",
        series_id=series_id,
        sort_order="desc",
        limit=limit,
    )
    return body["observations"]


# 이 시계열이 속한 release_id 조회 (release_id가 있어야 실제 발표일을 조회할 수 있다)
def get_series_release_id(series_id: str) -> int:
    body = _get("/series/release", series_id=series_id)
    return body["releases"][0]["id"]


# 해당 release의 실제 발표일(날짜만, 시각 없음)을 최신순으로 조회
def get_release_dates(release_id: int, *, limit: int = 1) -> list[dict]:
    body = _get(
        "/release/dates",
        release_id=release_id,
        sort_order="desc",
        limit=limit,
    )
    return body["release_dates"]
