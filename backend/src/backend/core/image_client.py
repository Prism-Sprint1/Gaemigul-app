# image_client.py
# 이미지 생성 호출 (전 도메인 공용). .env의 IMAGE_PROVIDER로 서비스를 고른다.
#   cloudflare (기본)  Cloudflare Workers AI FLUX.1 schnell, 무료 하루 10,000 뉴런(4단계 기준 장당 약 58뉴런, 단계 수에 비례)
#   pollinations      Pollinations gen.pollinations.ai, 모델은 POLLINATIONS_IMAGE_MODEL (시험용 - 결과가 별로면 IMAGE_PROVIDER를 지우면 Cloudflare로 돌아간다)

import base64
import time
from urllib.parse import quote

import httpx

from backend.core.config import get_settings

# 모델을 바꾸면 요청·응답 형식이 달라질 수 있다 (다른 모델은 이미지 바이트를 그대로 주기도 한다)
_MODEL = "@cf/black-forest-labs/flux-1-schnell"
_ENDPOINT = "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/" + _MODEL

# 생성 단계 수. schnell은 최대 8, 높일수록 세밀하지만 느리고 뉴런을 더 쓴다 (8은 4보다 사물이 뚜렷하고 장면이 잘 읽힌다. 보고서 이미지는 하루 2~4장이라 뉴런 부담이 작다)
_STEPS = 8

# 실패 시 재시도 횟수, 대기(초, 시도마다 배수로 늘어남), 요청 타임아웃(초 - 생성이 1.5~5초 걸린다)
# 429(요청 한도 초과)는 잠깐 뒤 풀리므로 더 길게 기다린다 (_RATE_LIMIT_WAIT_SECONDS x 시도 번호)
_RETRY_COUNT = 3
_RETRY_WAIT_SECONDS = 1.0
_RATE_LIMIT_WAIT_SECONDS = 5.0
_TIMEOUT_SECONDS = 60.0


# Pollinations 이미지 주소. 프롬프트는 경로에 URL 인코딩해서 넣고, 키는 Authorization 헤더로 보낸다(sk_ 비밀 키)
# 응답은 이미지 바이트 그대로 온다. 401 키 오류 / 402 잔액 부족 / 429 한도 초과(Retry-After 헤더)
_POLLINATIONS_ENDPOINT = "https://gen.pollinations.ai/image/{prompt}"

# Pollinations 요청 크기(Cloudflare와 같은 정사각형으로 맞춰 비교한다)와 타임아웃(초 - 상위 모델은 수십 초 걸릴 수 있다)
_POLLINATIONS_SIZE = 1024
_POLLINATIONS_TIMEOUT_SECONDS = 180.0


# 영어 프롬프트로 이미지를 만들어 이미지 바이트로 돌려준다
#   prompt  영어 장면 묘사 (한국어를 넣으면 내용과 무관한 그림이 나온다)
# 이미지 안에 글자를 정확히 쓰지 못하므로 프롬프트에 글자를 요구하지 않는다
# 5xx·429·연결 오류는 재시도하고 나머지 4xx는 바로 에러를 낸다. 키가 없으면 RuntimeError
def generate_image(prompt: str) -> bytes:
    if get_settings().image_provider == "pollinations":
        return _generate_with_pollinations(prompt)
    return _generate_with_cloudflare(prompt)


# Cloudflare Workers AI. 결과는 1024x1024 JPEG 고정이다 (width·height를 보내면 400 에러)
def _generate_with_cloudflare(prompt: str) -> bytes:
    settings = get_settings()
    if not settings.cloudflare_account_id or not settings.cloudflare_api_token:
        raise RuntimeError("CLOUDFLARE_ACCOUNT_ID / CLOUDFLARE_API_TOKEN이 .env에 없습니다. backend/.env에 추가해주세요.")

    last_error = None
    for attempt in range(_RETRY_COUNT):
        try:
            response = httpx.post(
                _ENDPOINT.format(account_id=settings.cloudflare_account_id),
                headers={"Authorization": f"Bearer {settings.cloudflare_api_token}"},
                json={"prompt": prompt, "steps": _STEPS},
                timeout=_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            # 응답: {"result": {"image": base64 JPEG}, "success": true, ...}
            return base64.b64decode(response.json()["result"]["image"])
        except httpx.HTTPStatusError as error:
            status = error.response.status_code
            if status < 500 and status != 429:
                raise
            last_error = error
        except httpx.TransportError as error:
            last_error = error

        if attempt < _RETRY_COUNT - 1:
            rate_limited = isinstance(last_error, httpx.HTTPStatusError) and last_error.response.status_code == 429
            time.sleep((_RATE_LIMIT_WAIT_SECONDS if rate_limited else _RETRY_WAIT_SECONDS) * (attempt + 1))

    raise last_error


# Pollinations. 모델은 POLLINATIONS_IMAGE_MODEL, 크기는 _POLLINATIONS_SIZE 정사각형
# 응답이 이미지가 아니면(오류 문구 등) ValueError. 429면 Retry-After 헤더만큼(없으면 _RATE_LIMIT_WAIT_SECONDS x 시도 번호) 기다린다
def _generate_with_pollinations(prompt: str) -> bytes:
    settings = get_settings()
    if not settings.pollinations_api_key:
        raise RuntimeError("POLLINATIONS_API_KEY가 .env에 없습니다. backend/.env에 추가해주세요.")

    last_error = None
    for attempt in range(_RETRY_COUNT):
        wait = _RETRY_WAIT_SECONDS * (attempt + 1)
        try:
            response = httpx.get(
                _POLLINATIONS_ENDPOINT.format(prompt=quote(prompt, safe="")),
                headers={"Authorization": f"Bearer {settings.pollinations_api_key}"},
                params={"model": settings.pollinations_image_model, "width": _POLLINATIONS_SIZE, "height": _POLLINATIONS_SIZE},
                timeout=_POLLINATIONS_TIMEOUT_SECONDS,
                follow_redirects=True,
            )
            response.raise_for_status()
            if not response.headers.get("content-type", "").startswith("image/"):
                raise ValueError(f"Pollinations 응답이 이미지가 아닙니다 - {response.headers.get('content-type')}: {response.text[:200]}")
            return response.content
        except httpx.HTTPStatusError as error:
            status = error.response.status_code
            if status < 500 and status != 429:
                raise
            last_error = error
            if status == 429:
                retry_after = error.response.headers.get("retry-after", "")
                wait = float(retry_after) if retry_after.replace(".", "", 1).isdigit() else _RATE_LIMIT_WAIT_SECONDS * (attempt + 1)
        except httpx.TransportError as error:
            last_error = error

        if attempt < _RETRY_COUNT - 1:
            time.sleep(wait)

    raise last_error
