# briefing_service.py
# 수집한 데이터로 LLM 브리핑과 불개미(주식 입문자) 요약을 만든다
#
# 두 단계로 부른다
#   1) 브리핑: 수집 데이터 -> 헤드라인 + 부제 + 포인트 3개
#   2) 불개미 요약: 위 브리핑 -> 같은 내용을 쉬운 말로 다시 쓴 것 3개
#
# 순서가 중요하다. 각각 원본 데이터에서 따로 만들면 두 요약이 서로 다른 얘기를 할 수 있다.
# 프롬프트 문구는 prompts.py에 있다.

import json
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from backend.core import llm_client
from backend.domain.timeline.services import prompts

_KST = ZoneInfo("Asia/Seoul")

# 브리핑에 넣을 포인트 개수 (화면 카드가 3장)
_POINT_COUNT = 3


# LLM에게 넘길 수집 데이터를 JSON 문자열로 만든다
#
# 확정 수치(시세 API에서 직접 받은 값)와 뉴스를 나눠서 넘기는 게 핵심이다.
# 프롬프트에서 "뉴스 속 숫자는 기사 시점 값"이라고 구분해 쓰게 하려면 입력부터 갈라져 있어야 한다
def _build_data(indicators: list[dict], sectors: list[dict], news: list[dict]) -> str:
    payload = {
        "확정 수치": {
            "지표": [{"이름": item["name"], "가격": item["price"], "등락률": item["change_rate"]} for item in indicators],
            "주도 섹터": [
                {
                    "업종": sector["name"],
                    "등락률": sector["change_rate"],
                    "종목": [{"이름": stock["name"], "등락률": stock["change_rate"], "구분": stock["label"]} for stock in sector["stocks"]],
                }
                for sector in sectors
            ],
        },
        "뉴스": [{"발행시각": f"{item['published_at']:%m-%d %H:%M}", "제목": item["title"], "요약": item["summary"]} for item in news],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


# 브리핑을 만든다
# 실패하면 None을 돌려준다 - 브리핑이 없어도 지표·뉴스·주도 섹터는 화면에 나가야 하기 때문이다
def _generate_briefing(time_slot: str, data: str, now: datetime) -> dict | None:
    try:
        answer = llm_client.generate_json(
            prompts.BRIEFING_PROMPT.format(
                time_slot=time_slot,
                title=prompts.SLOT_TITLES[time_slot],
                focus=prompts.SLOT_FOCUS[time_slot],
                now=f"{now:%Y-%m-%d %H:%M}",
                data=data,
            )
        )
    except (RuntimeError, ValueError, KeyError, httpx.HTTPError) as error:
        print(f"[경고] 브리핑 생성 실패 - {error}")
        return None

    points = [point for point in answer.get("points", []) if isinstance(point, dict) and point.get("title") and point.get("body")]
    if not answer.get("headline") or not points:
        print("[경고] 브리핑 응답에 필요한 값이 없습니다.")
        return None

    return {
        "headline": answer["headline"],
        "subtitle": answer.get("subtitle") or "",
        "points": [{"seq": seq, "title": point["title"], "body": point["body"]} for seq, point in enumerate(points[:_POINT_COUNT], start=1)],
    }


# 브리핑을 입문자용으로 다시 쓴다
# 브리핑이 없으면 만들 재료가 없으므로 빈 목록을 돌려준다
def _generate_beginner_guides(briefing: dict | None) -> list[dict]:
    if briefing is None:
        return []

    try:
        answer = llm_client.generate_json(prompts.BEGINNER_PROMPT.format(briefing=json.dumps(briefing, ensure_ascii=False), glossary=prompts.GLOSSARY_TEXT))
    except (RuntimeError, ValueError, KeyError, httpx.HTTPError) as error:
        print(f"[경고] 불개미 요약 생성 실패 - {error}")
        return []

    points = [point for point in answer.get("points", []) if isinstance(point, dict) and point.get("title") and point.get("body")]
    return [
        {
            "seq": seq,
            "title": point["title"],
            "body": point["body"],
            # 태그는 DB에 쉼표로 이어붙여 한 칸에 저장한다(timeline_beginner_guide.tags)
            "tags": [str(tag) for tag in point.get("tags", []) if tag][:3],
        }
        for seq, point in enumerate(points[:_POINT_COUNT], start=1)
    ]


# 브리핑과 불개미 요약을 한 번에 만든다. timeline_service가 호출한다
#
# LLM을 두 번 부르기 때문에 30초에서 1분 정도 걸린다.
# 실패해도 예외를 올리지 않고 빈 값을 돌려준다 - 브리핑이 없다고 슬롯 전체가 없어지면 안 된다
#
# 반환: (브리핑 또는 None, 불개미 요약 목록)
def generate(time_slot: str, *, indicators: list[dict], sectors: list[dict], news: list[dict], now: datetime | None = None) -> tuple[dict | None, list[dict]]:
    data = _build_data(indicators, sectors, news)
    briefing = _generate_briefing(time_slot, data, now or datetime.now(_KST))
    return briefing, _generate_beginner_guides(briefing)
