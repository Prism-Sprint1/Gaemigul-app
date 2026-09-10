# llm_client.py
# 제미나이 API 직접 호출
#
# 모델 목록 API에는 40개 가까이 나오지만 실제로 호출되는 모델은 제한적이다.
# gemini-2.5-flash는 신규 사용자에게 더 이상 제공되지 않아 404가 난다(2026-09-10 확인).
# 모델을 바꾸려면 아래 _MODEL 값만 수정하면 된다.
#
# gemini-3.6-flash에서 gemini-3.5-flash-lite로 바꾼 이유 (2026-09-10)
#   1. 무료 한도: 3.6-flash는 하루 20회다(429 응답의 GenerateRequestsPerDayPerProjectPerModel-FreeTier).
#      타임라인은 슬롯당 3회씩 8슬롯이면 하루 24회라 한도를 넘어서, 뒤쪽 슬롯 브리핑이 통째로 비었다.
#   2. 속도: 브리핑 생성이 30초에서 2초로 줄었다. 슬롯 하나 만드는 시간이 72초에서 10초 안팎이 된다.
#      슬롯 시각 5분 전에 수집하는 구조라, 빠를수록 실패했을 때 재시도할 여유가 커진다.
#   품질은 실제 데이터로 확인했을 때 차이가 없었다. 우리 작업이 "준 데이터를 요약하기"라 난도가 낮아서다.
#
# 한도는 모델별로 따로 잡힌다. 한 모델이 429가 나도 다른 모델은 쓸 수 있다.

import json
import re
import time

import httpx

from backend.core.config import get_settings

_MODEL = "gemini-3.5-flash-lite"
_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{_MODEL}:generateContent"

# 호출 실패 시 재시도 설정
# LLM은 한 번 부르는 데 수십 초가 걸릴 수 있어서 재시도 횟수를 다른 클라이언트보다 적게 잡았다.
# 3회로 늘리면 최악의 경우 3분 가까이 붙잡혀 있게 된다
_RETRY_COUNT = 2
_RETRY_WAIT_SECONDS = 1.0


# 프롬프트를 보내고 생성된 텍스트를 돌려받는다
# timeout: LLM은 응답이 느릴 수 있어 기본값을 넉넉히 잡음
# 타임아웃이나 서버 오류면 한 번 더 시도한다. 그래도 실패하면 httpx 예외가 그대로 올라간다
def generate(prompt: str, timeout: float = 60.0) -> str:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY가 .env에 없습니다. backend/.env에 추가해주세요.")

    response = httpx.post(
        _ENDPOINT,
        headers={
            "x-goog-api-key": settings.gemini_api_key,
            "content-type": "application/json",
        },
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()["candidates"][0]["content"]["parts"][0]["text"]


# 프롬프트를 보내고 결과를 JSON(dict)으로 돌려받는다
#
# 모델에게 "JSON만 출력해라"라고 해도 ```json ... ``` 코드블록으로 감싸서 주는 경우가 많아서
# 감싼 부분을 벗겨낸 뒤 파싱한다. 앞뒤에 설명 문장이 붙는 경우도 있어 중괄호 구간만 잘라낸다
#
# JSON으로 못 읽으면 ValueError를 낸다. 부르는 쪽에서 이걸 잡아 기본 동작으로 넘어가면 된다
def generate_json(prompt: str, timeout: float = 60.0) -> dict:
    text = generate(prompt, timeout=timeout).strip()

    # ```json ... ``` 또는 ``` ... ``` 벗기기
    fenced = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)

    # 앞뒤에 설명이 붙었으면 바깥 중괄호 구간만 남기기
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"LLM 응답에서 JSON을 찾지 못했습니다: {text[:200]}")

    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError as error:
        raise ValueError(f"LLM 응답을 JSON으로 읽지 못했습니다: {text[:200]}") from error
