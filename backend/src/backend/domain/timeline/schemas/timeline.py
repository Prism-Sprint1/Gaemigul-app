# timeline.py
# GET /timeline/slot/{slot_key} 응답 형태(DTO)
#
# 지금은 DB를 거치지 않고 수집한 값을 바로 조립해서 내려준다.
# 나중에 저장 로직이 붙어도 이 응답 형태는 그대로 쓸 수 있게 테이블 구조와 필드 이름을 맞춰뒀다.

from datetime import datetime

from pydantic import BaseModel


# 주도 섹터 카드 안에 들어가는 대표 종목 (timeline_leading_sector_stock 테이블과 같은 구성)
class LeadingSectorStockItem(BaseModel):
    name: str  # 종목명
    change_rate: float  # 등락률(%). 0보다 크면 상승, 작으면 하락
    label: str  # "상승 1위" / "거래 1위" / "상승·거래 1위"


# 주도 섹터 카드 하나 (timeline_leading_sector 테이블과 같은 구성)
class LeadingSectorItem(BaseModel):
    code: str  # 업종코드. 화면에는 안 쓰고 디버깅·조회용
    name: str  # 업종명
    change_rate: float  # 업종 등락률(%)
    stocks: list[LeadingSectorStockItem]  # 대표 종목 1~2개


# LLM 브리핑 포인트 한 줄 (timeline_briefing_insight 테이블과 같은 구성)
class BriefingPointItem(BaseModel):
    seq: int  # 표시 순서 (1, 2, 3)
    title: str
    body: str


# 불개미(주식 입문자) 요약 한 줄 (timeline_beginner_guide 테이블과 같은 구성)
class BeginnerGuideItem(BaseModel):
    seq: int
    title: str
    body: str
    tags: list[str]  # DB에는 쉼표로 이어붙여 한 칸에 저장한다


# 뉴스 한 줄 (timeline_news 테이블과 같은 구성)
class NewsItem(BaseModel):
    seq: int  # 표시 순서 (1부터). 중요도가 높은 기사가 1번
    title: str
    summary: str
    url: str
    published_at: datetime  # 확인용. 지금 테이블에는 저장하지 않는다


# 지표 한 줄 (timeline_indicator 테이블과 같은 구성). 07:30 슬롯에만 들어간다
class SlotIndicatorItem(BaseModel):
    code: str
    name: str
    price: float
    change_rate: float


# 장중 변화 한 줄 (timeline_intraday_change 테이블과 같은 구성). 15:30 슬롯에만 들어간다
class IntradayChangeItem(BaseModel):
    name: str
    morning_price: float  # 07:30 슬롯에 저장된 가격
    closing_price: float  # 15:30 시점 가격
    change_rate: float  # 07:30 대비 변동폭(%)


# 슬롯 하나의 전체 응답
class TimelineSlotResponse(BaseModel):
    slot_key: str  # URL에 쓰는 값 ("0730")
    time_slot: str  # DB에 저장하는 값 ("07:30")
    title: str  # 화면에 보여줄 시간대 명칭 ("글로벌 시황")
    collected_at: datetime  # 이 응답을 만든 시각
    briefing_headline: str | None  # LLM 생성 실패 시 None
    briefing_subtitle: str | None
    briefing_points: list[BriefingPointItem]  # 최대 3개
    beginner_guides: list[BeginnerGuideItem]  # 최대 3개
    leading_sectors: list[LeadingSectorItem]  # 07:30 / 08:30 슬롯은 빈 배열
    news: list[NewsItem]
    indicators: list[SlotIndicatorItem]  # 07:30 슬롯 외에는 빈 배열
    intraday_changes: list[IntradayChangeItem]  # 15:30 슬롯 외에는 빈 배열
