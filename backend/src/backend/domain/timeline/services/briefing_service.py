# briefing_service.py
# 수집한 데이터로 LLM 브리핑과 불개미(주식 입문자) 해설을 만든다.
#   1) 브리핑: 수집 데이터 -> 헤드라인 + 부제 + 포인트 3개
#   2) 불개미 해설: 수집 데이터 + 브리핑 -> 왜 그런지 풀어 설명한 문단 3개
# 프롬프트 문구는 prompts.py에 있다.

import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from backend.core import llm_client
from backend.domain.timeline.services import prompts

_KST = ZoneInfo("Asia/Seoul")

logger = logging.getLogger(__name__)

# 브리핑 포인트·해설 문단 개수. 바꾸면 저장되는 개수가 바뀐다 (프롬프트의 출력 형식도 같이 맞출 것)
_POINT_COUNT = 3


# LLM 입력용 JSON 문자열을 만든다. 슬롯마다 채워진 항목만 들어간다
#   지표(07:30) / 장중 변화(15:30) / 주도 섹터(정규장 슬롯) / 급상승 종목(정규장 밖 슬롯) / 뉴스
# 시세 값은 "확정 수치", 기사는 "뉴스"로 나눈다. 프롬프트가 둘을 구분해서 쓰게 하기 위해서다
# 새 재료를 LLM에 넘기려면 확정 딕셔너리에 항목을 추가한다
def _build_data(indicators: list[dict], sectors: list[dict], top_gainers: list[dict], intraday_changes: list[dict], news: list[dict]) -> str:
    확정 = {
        "지표": [{"이름": item["name"], "가격": item["price"], "등락률": item["change_rate"]} for item in indicators],
        "장중 변화": [
            {"이름": row["name"], "07:30 가격": row["morning_price"], "마감 가격": row["closing_price"], "변동률": row["change_rate"]}
            for row in intraday_changes
        ],
        "주도 섹터": [
            {
                "업종": sector["name"],
                "등락률": sector["change_rate"],
                "종목": [{"이름": stock["name"], "등락률": stock["change_rate"], "구분": stock["label"]} for stock in sector["stocks"]],
            }
            for sector in sectors
        ],
        "급상승 종목": [{"이름": row["name"], "등락률": row["change_rate"], "가격": row["price"]} for row in top_gainers],
    }

    # 빈 항목은 넣지 않는다 (빈 배열이 있으면 LLM이 "데이터가 없다" 쪽으로 글을 짧게 쓴다)
    payload = {
        "확정 수치": {key: value for key, value in 확정.items() if value},
        "뉴스": [{"발행시각": f"{item['published_at']:%m-%d %H:%M}", "제목": item["title"], "요약": item["summary"]} for item in news],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


# 브리핑을 만든다. 실패하면 None (브리핑이 없어도 슬롯의 나머지는 저장된다)
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
        logger.warning("브리핑 생성 실패 - %s: %s", type(error).__name__, error)
        return None

    points = [point for point in answer.get("points", []) if isinstance(point, dict) and point.get("title") and point.get("body")]
    if not answer.get("headline") or not points:
        logger.warning("브리핑 응답에 필요한 값이 없습니다.")
        return None

    return {
        "headline": answer["headline"],
        "subtitle": answer.get("subtitle") or "",
        "points": [{"seq": seq, "title": point["title"], "body": point["body"]} for seq, point in enumerate(points[:_POINT_COUNT], start=1)],
    }


# 불개미 해설을 만든다. 재료는 수집 데이터(data)와 브리핑
# 브리핑이 없거나 실패하면 빈 목록
def _generate_beginner_guides(data: str, briefing: dict | None) -> list[dict]:
    if briefing is None:
        return []

    try:
        answer = llm_client.generate_json(prompts.BEGINNER_PROMPT.format(data=data, briefing=json.dumps(briefing, ensure_ascii=False)))
    except (RuntimeError, ValueError, KeyError, httpx.HTTPError) as error:
        logger.warning("불개미 해설 생성 실패 - %s: %s", type(error).__name__, error)
        return []

    points = [point for point in answer.get("points", []) if isinstance(point, dict) and point.get("title") and point.get("body")]
    return [
        {
            "seq": seq,
            "title": point["title"],
            "body": point["body"],
            # 태그는 최대 3개. DB에는 쉼표로 이어붙여 한 칸에 저장한다
            "tags": [str(tag) for tag in point.get("tags", []) if tag][:3],
        }
        for seq, point in enumerate(points[:_POINT_COUNT], start=1)
    ]


# 브리핑과 불개미 해설을 한 번에 만든다. timeline_service가 호출한다
# 실패해도 예외를 올리지 않는다. 반환: (브리핑 또는 None, 해설 목록)
def generate(
    time_slot: str,
    *,
    indicators: list[dict],
    sectors: list[dict],
    top_gainers: list[dict],
    intraday_changes: list[dict],
    news: list[dict],
    now: datetime | None = None,
) -> tuple[dict | None, list[dict]]:
    data = _build_data(indicators, sectors, top_gainers, intraday_changes, news)
    briefing = _generate_briefing(time_slot, data, now or datetime.now(_KST))
    return briefing, _generate_beginner_guides(data, briefing)
