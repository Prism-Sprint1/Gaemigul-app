# check_llm_output.py
# LLM 브리핑·불개미 요약 결과를 눈으로 확인하는 스크립트
#
# 프롬프트(services/prompts.py)를 고친 뒤 결과가 어떻게 바뀌는지 볼 때 쓴다.
# 서버를 띄우지 않고 바로 함수를 부르기 때문에 확인이 빠르다.
#
# 사용법
#   uv run python check_llm_output.py            (07:30 슬롯)
#   uv run python check_llm_output.py 1200       (12:00 슬롯)
#   uv run python check_llm_output.py 1200 news  (뉴스 선별 결과까지 같이 보기)
#
# 슬롯 하나에 LLM을 두 번 부르므로 1분 안팎 걸린다.
# 프롬프트 검토가 끝나면 이 파일은 지워도 된다

import sys

sys.path.insert(0, "src")

from backend.domain.timeline.services import timeline_service


def main() -> None:
    slot_key = sys.argv[1] if len(sys.argv) > 1 else "0730"
    show_news = len(sys.argv) > 2 and sys.argv[2] == "news"

    print(f"{slot_key} 슬롯 생성 중... (LLM 호출 때문에 1분 안팎 걸립니다)")
    slot = timeline_service.get_slot(slot_key)

    print()
    print("=" * 78)
    print(f"  {slot.title}  {slot.time_slot}")
    print("=" * 78)

    if slot.briefing_headline is None:
        print("  브리핑 생성 실패 (위에 찍힌 경고 문구 확인)")
    else:
        print(f"  ⚡ {slot.briefing_headline}")
        print(f"     {slot.briefing_subtitle}")
        print()
        for point in slot.briefing_points:
            print(f"  POINT {point.seq:02d}  {point.title}")
            for line in _wrap(point.body):
                print(f"            {line}")
            print()

    print("-" * 78)
    print("  불개미 3줄 핵심 요약")
    print("-" * 78)
    if not slot.beginner_guides:
        print("  생성된 요약 없음")
    for guide in slot.beginner_guides:
        tags = "  ".join(f"#{tag}" for tag in guide.tags)
        print(f"  POINT {guide.seq:02d}  {guide.title}   {tags}")
        for line in _wrap(guide.body):
            print(f"            {line}")
        print()

    print("-" * 78)
    print(f"  참고 - 지표 {len(slot.indicators)}개 / 주도 섹터 {len(slot.leading_sectors)}개 / 뉴스 {len(slot.news)}건")
    print("-" * 78)
    for item in slot.indicators:
        print(f"  {item.name:<10} {item.price:>12,.2f}  {item.change_rate:+.2f}%")
    for sector in slot.leading_sectors:
        stocks = ", ".join(f"{stock.name}({stock.label}) {stock.change_rate:+.2f}%" for stock in sector.stocks)
        print(f"  {sector.name} {sector.change_rate:+.2f}% - {stocks}")
    if show_news:
        for news in slot.news:
            print(f"  {news.seq}. [{news.published_at:%m-%d %H:%M}] {news.title}")


# 긴 문장을 폭에 맞춰 끊는다 (한글은 두 칸으로 계산)
def _wrap(text: str, width: int = 62) -> list[str]:
    lines, current = [], ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if sum(2 if ord(char) > 127 else 1 for char in candidate) > width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


if __name__ == "__main__":
    main()
