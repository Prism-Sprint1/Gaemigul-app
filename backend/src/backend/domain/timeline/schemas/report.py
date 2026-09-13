# report.py
# 브리핑 탭 일간·주간 보고서 응답 형태(DTO). GET /timeline/report, POST /timeline/report/daily·weekly가 쓴다.
# 필드 이름은 models/report.py의 테이블 칼럼과 맞춘다. 필드를 추가하면 report_service.to_response도 고칠 것
# 금액은 전부 백만원 단위 숫자로 내려준다 (억·조 표기는 프런트가 한다)
# LLM이 실패한 보고서는 문구 필드가 None이고 목록이 비어 있다 (수치는 채워져 있을 수 있다)

from datetime import date, datetime

from pydantic import BaseModel


# 섹션 하나 (1 핵심 이슈 / 2 수급과 변동성 / 3 주목할 섹터)
class ReportSectionItem(BaseModel):
    seq: int  # 섹션 번호 (1, 2, 3)
    title: str | None
    description: str | None
    image_url: str | None  # 섹션1만 있다
    points: list[str]  # 핵심 요약 3개


# 섹션2 차트의 분기 하나
class ReportQuarterItem(BaseModel):
    label: str  # "26/Q3"
    usd_krw: float | None  # 원달러 환율
    foreign_net_buy: int | None  # 외국인 순매수 합계(백만원)
    is_current: bool  # 진행 중인 분기


# 섹션3 섹터 카드 하나
class ReportSectorItem(BaseModel):
    sector_name: str  # 업종명
    change_rate: float | None  # 업종 등락률(%). 일간은 전일 대비, 주간은 전주 대비
    rising_count: int | None  # 상승 종목 수 (주간은 None일 수 있다)
    total_count: int | None  # 업종 전체 종목 수
    rising_ratio: float | None  # 상승 종목 비율(%) = rising_count / total_count
    trade_amount: int | None  # 거래대금(백만원). 일간은 당일, 주간은 그 주
    prev_trade_amount: int | None  # 비교 거래대금(백만원). 일간은 전일, 주간은 전주
    trade_amount_change_rate: float | None  # 거래대금 증감률(%)


# 결론 키워드 하나
class ReportKeywordItem(BaseModel):
    title: str
    description: str


# 결론 어려운 용어 하나
class ReportTermItem(BaseModel):
    term: str
    description: str
    source: str  # "GLOSSARY"(사전) / "LLM"(사전에 없어 LLM이 작성)


# 보고서 전체 응답
class ReportResponse(BaseModel):
    report_type: str  # "DAILY" / "WEEKLY"
    start_date: date  # 일간은 그날, 주간은 그 주 첫 거래일
    end_date: date  # 일간은 그날, 주간은 그 주 마지막 거래일
    published_at: datetime | None  # 발행 시각 (KST). 문구 생성 전이면 None
    title: str | None
    summary: str | None  # 메인 한 줄 요약
    main_image_url: str | None
    sections: list[ReportSectionItem]  # 메인 화면의 섹션 타이틀 3개도 여기서 쓴다
    foreign_net_buy: int | None  # 섹션2 외국인 순매수(백만원). 주간은 주간 합계
    institution_net_buy: int | None
    individual_net_buy: int | None
    vkospi: float | None  # 섹션2 VKOSPI
    vkospi_change_rate: float | None  # 일간은 전일 대비, 주간은 전주 대비(%)
    quarters: list[ReportQuarterItem]  # 섹션2 차트 6개, 오래된 분기부터
    sectors: list[ReportSectorItem]  # 섹션3 카드 최대 3개
    conclusion: str | None  # 결론 한 줄 요약
    keywords: list[ReportKeywordItem]  # 3개
    terms: list[ReportTermItem]  # 3개
