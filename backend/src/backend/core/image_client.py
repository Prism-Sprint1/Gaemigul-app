# image_client.py
# Cloudflare Workers AI 이미지 생성 호출 (전 도메인 공용). 모델은 FLUX.1 schnell, 무료 하루 10,000 뉴런(장당 약 58뉴런).

import base64
import time

import httpx

from backend.core.config import get_settings

# 모델을 바꾸면 요청·응답 형식이 달라질 수 있다 (다른 모델은 이미지 바이트를 그대로 주기도 한다)
_MODEL = "@cf/black-forest-labs/flux-1-schnell"
_ENDPOINT = "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/" + _MODEL

# 생성 단계 수. schnell은 최대 8, 높일수록 세밀하지만 느리고 뉴런을 더 쓴다
_STEPS = 4

# 실패 시 재시도 횟수, 대기(초, 시도마다 배수로 늘어남), 요청 타임아웃(초 - 생성이 1.5~5초 걸린다)
_RETRY_COUNT = 3
_RETRY_WAIT_SECONDS = 1.0
_TIMEOUT_SECONDS = 60.0


# 영어 프롬프트로 이미지를 만들어 JPEG 바이트로 돌려준다
#   prompt  영어 장면 묘사 (한국어를 넣으면 내용과 무관한 그림이 나온다)
# 결과는 1024x1024 정사각형 고정이다 (width·height를 보내면 400 에러)
# 이미지 안에 글자를 정확히 쓰지 못하므로 프롬프트에 글자를 요구하지 않는다
# 5xx·연결 오류는 재시도하고 4xx는 바로 에러를 낸다. 키가 없으면 RuntimeError
def generate_image(prompt: str) -> bytes:
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
            if error.response.status_code < 500:
                raise
            last_error = error
        except httpx.TransportError as error:
            last_error = error

        if attempt < _RETRY_COUNT - 1:
            time.sleep(_RETRY_WAIT_SECONDS * (attempt + 1))

    raise last_error
