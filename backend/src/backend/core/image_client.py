# Pollinations 이미지 생성. 보고서 배너는 1200x400, 모델은 POLLINATIONS_IMAGE_MODEL에서 변경한다.
# 402 잔액 부족은 재시도하지 않는다. 서버 키는 Authorization 헤더에만 보낸다.

import time
from io import BytesIO
from pathlib import Path
from urllib.parse import quote

import httpx
from PIL import Image, ImageDraw, ImageFont

from backend.core.config import get_settings

_POLLINATIONS_ENDPOINT = "https://gen.pollinations.ai/image/{prompt}"
_WIDTH, _HEIGHT = 1200, 400
_POLLINATIONS_TIMEOUT_SECONDS = 180.0
_RETRY_COUNT = 3
_RETRY_WAIT_SECONDS = 1.0
_RATE_LIMIT_WAIT_SECONDS = 5.0
_JPEG_QUALITY = 88

_FONT_CANDIDATES = (
    ("/System/Library/Fonts/AppleSDGothicNeo.ttc", 14),  # ExtraBold
    ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", 0),
    ("/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc", 0),
)


# 파일 시그니처로 확장자와 Content-Type을 정한다. 지원하지 않는 응답은 업로드하지 않는다.
def image_format(content: bytes) -> tuple[str, str]:
    if content.startswith(b"\xff\xd8\xff"):
        return "jpg", "image/jpeg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png", "image/png"
    if content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        return "webp", "image/webp"
    raise ValueError("지원하지 않는 이미지 형식입니다")


def _korean_font(size: int) -> ImageFont.FreeTypeFont:
    for candidate, index in _FONT_CANDIDATES:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size, index=index)
    raise RuntimeError("한글 이미지 합성 폰트가 없습니다. Noto Sans CJK Bold를 설치해주세요.")


def _fit_font(draw: ImageDraw.ImageDraw, text: str, width: int, height: int, maximum: int) -> ImageFont.FreeTypeFont:
    for size in range(maximum, 11, -1):
        font = _korean_font(size)
        box = draw.textbbox((0, 0), text, font=font, stroke_width=1)
        if box[2] - box[0] <= width and box[3] - box[1] <= height:
            return font
    return _korean_font(12)


def _draw_centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    box: tuple[int, int, int, int],
    maximum: int,
    *,
    horizontal_padding: int = 8,
    vertical_padding: int = 4,
) -> None:
    left, top, right, bottom = box
    font = _fit_font(draw, text, right - left - horizontal_padding * 2, bottom - top - vertical_padding * 2, maximum)
    bounds = draw.textbbox((0, 0), text, font=font, stroke_width=1)
    x = left + (right - left - (bounds[2] - bounds[0])) / 2 - bounds[0]
    y = top + (bottom - top - (bounds[3] - bounds[1])) / 2 - bounds[1]
    ink = (68, 36, 20)
    draw.text((x, y), text, font=font, fill=ink)


def _draw_wood_plaque(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], *, radius: int, pegs: bool) -> None:
    """제목과 키워드를 같은 계열의 입체 목재 명패로 그린다."""
    left, top, right, bottom = box
    draw.rounded_rectangle((left + 5, top + 7, right + 5, bottom + 7), radius=radius, fill=(72, 42, 25))
    draw.rounded_rectangle(box, radius=radius, fill=(228, 181, 121), outline=(137, 83, 43), width=3)
    draw.rounded_rectangle((left + 5, top + 4, right - 5, bottom - 5), radius=max(4, radius - 4), outline=(245, 210, 158), width=2)
    # 일정한 직선 대신 길이가 다른 얇은 결을 넣어 플라스틱 판처럼 보이지 않게 한다.
    for offset, inset in ((14, 28), (29, 17), (45, 36), (62, 22)):
        y = top + offset
        if y < bottom - 8:
            draw.line((left + inset, y, right - inset - 9, y), fill=(205, 151, 94), width=1)
    if pegs:
        for x in (left + 16, right - 16):
            draw.ellipse((x - 5, top + 10, x + 5, top + 20), fill=(114, 67, 38), outline=(82, 47, 28), width=1)


def _title_box(draw: ImageDraw.ImageDraw, headline: str) -> tuple[int, int, int, int]:
    """제목 길이에 맞추되 화면·글자 양쪽에 일정한 여백을 둔 작은 목재 간판을 계산한다."""
    side_margin = 64
    horizontal_padding = 28
    max_width = _WIDTH - side_margin * 2
    font = _fit_font(draw, headline, max_width - horizontal_padding * 2, 44, 38)
    bounds = draw.textbbox((0, 0), headline, font=font)
    text_width = bounds[2] - bounds[0]
    text_height = bounds[3] - bounds[1]
    width = min(max_width, max(300, text_width + horizontal_padding * 2))
    height = min(72, max(58, text_height + 22))
    left = (_WIDTH - width) // 2
    return left, 12, left + width, 12 + height


def _fill_frame_with_scene(image: Image.Image) -> Image.Image:
    """모델이 만든 흰 하단 띠를 감지하면 띠 위 장면을 세로로 확장해 프레임 전체를 채운다."""
    pixels = image.load()
    white_start = None
    consecutive = 0
    for y in range(250, _HEIGHT):
        sampled = [pixels[x, y] for x in range(0, _WIDTH, 8)]
        white_ratio = sum(min(pixel) >= 242 and max(pixel) - min(pixel) <= 12 for pixel in sampled) / len(sampled)
        consecutive = consecutive + 1 if white_ratio >= 0.9 else 0
        if consecutive >= 4:
            white_start = y - 3
            break
    if white_start is None:
        return image
    return image.crop((0, 0, _WIDTH, max(260, white_start))).resize((_WIDTH, _HEIGHT), Image.Resampling.LANCZOS)


def add_korean_labels(content: bytes, *, headline: str, labels: list[str]) -> bytes:
    """Pollinations 결과 위에 고정 레이아웃 한글 간판을 합성해 압축 JPEG로 반환한다."""
    image = Image.open(BytesIO(content)).convert("RGB")
    if image.size != (_WIDTH, _HEIGHT):
        image = image.resize((_WIDTH, _HEIGHT), Image.Resampling.LANCZOS)
    image = _fill_frame_with_scene(image)
    draw = ImageDraw.Draw(image)

    # 상단 제목은 장면 속 목재 간판처럼 보이도록 그림자·나뭇결·못 장식을 함께 그린다.
    title_box = _title_box(draw, headline)
    _draw_wood_plaque(draw, title_box, radius=11, pegs=True)
    _draw_centered_text(draw, headline, title_box, 38, horizontal_padding=28, vertical_padding=9)

    # 키워드는 배경을 가리지 않는 개별 목재 명패로 올리고 제목과 같은 서체·재질을 쓴다.
    visible = [label for label in labels if label][:4]
    if visible:
        gap, plaque_width, plaque_height = 18, 240, 52
        total = len(visible) * plaque_width + (len(visible) - 1) * gap
        start = (_WIDTH - total) // 2
        for index, label in enumerate(visible):
            left = start + index * (plaque_width + gap)
            box = (left, 332, left + plaque_width, 332 + plaque_height)
            _draw_wood_plaque(draw, box, radius=9, pegs=False)
            _draw_centered_text(draw, label, box, 27)

    output = BytesIO()
    image.save(output, format="JPEG", quality=_JPEG_QUALITY, optimize=True, progressive=True, subsampling=1)
    return output.getvalue()


# 그림 설명으로 이미지 바이트를 만든다. 5xx·429·연결 오류만 재시도한다.
def generate_image(prompt: str) -> bytes:
    settings = get_settings()
    if not settings.pollinations_api_key:
        raise RuntimeError("POLLINATIONS_API_KEY가 .env에 없습니다.")

    last_error = None
    for attempt in range(_RETRY_COUNT):
        wait = _RETRY_WAIT_SECONDS * (attempt + 1)
        try:
            response = httpx.get(
                _POLLINATIONS_ENDPOINT.format(prompt=quote(prompt, safe="")),
                headers={"Authorization": f"Bearer {settings.pollinations_api_key}"},
                params={"model": settings.pollinations_image_model, "width": _WIDTH, "height": _HEIGHT},
                timeout=_POLLINATIONS_TIMEOUT_SECONDS,
                follow_redirects=True,
            )
            response.raise_for_status()
            if not response.headers.get("content-type", "").startswith("image/"):
                raise ValueError(f"Pollinations 응답이 이미지가 아닙니다 - {response.headers.get('content-type')}: {response.text[:200]}")
            image_format(response.content)
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
