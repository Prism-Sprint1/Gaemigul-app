# models > report.py
# 브리핑 탭 일간·주간 보고서 테이블 7개 (SQLAlchemy ORM 모델).
#
# [테이블 관계] 보고서 하나에 아래 자식 행들이 붙는다
#   timeline_report ─┬─ timeline_report_section        섹션 3행
#                    │     └─ timeline_report_point    핵심 요약 3행씩
#                    ├─ timeline_report_quarter        차트 분기 6행
#                    ├─ timeline_report_sector         섹터 카드 3행
#                    ├─ timeline_report_keyword        결론 키워드 3행
#                    └─ timeline_report_term           어려운 용어 3행
#
# [조회 기준] 프런트가 날짜를 주면
#   일간: report_type="DAILY"  이고 start_date = 그 날짜
#   주간: report_type="WEEKLY" 이고 start_date <= 그 날짜 <= end_date
#
# [저장 순서] 수치 칼럼을 먼저 채우고 LLM 문구 칼럼은 나중에 채운다.
#   그래서 LLM 문구 칼럼은 전부 NULL을 허용한다 (LLM이 실패해도 수치는 남는다)
#
# 금액 단위는 전부 백만원이다 (KIS 투자자 매매동향·업종 지수 응답 단위). 분기 합산이 수십조 원까지 커져서 BigInteger로 둔다
#
# created_at은 파이썬 기본값(_now_kst)과 DB 기본값(server_default)을 둘 다 건다.
#   한쪽만 있으면 옛 코드로 돌고 있는 서버가 값을 안 보낼 때 NOT NULL 위반이 난다
#
# 테이블을 추가하면: 여기 모델 추가 -> Supabase에 테이블 생성(create_tables.py)
#   -> report_repository._EAGER_LOAD에 등록 -> 저장(report_repository)·응답(schemas/report.py, report_service.to_response) 코드 추가

from datetime import date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Float, ForeignKey, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base

_KST = ZoneInfo("Asia/Seoul")

# DB 쪽 created_at 기본값 (시간대 없는 한국 시간)
_KST_NOW_SQL = text("(now() AT TIME ZONE 'Asia/Seoul')")


# created_at 파이썬 기본값. 시간대 없는 한국 시간으로 저장한다 (타임라인 테이블과 기준을 맞춘다)
def _now_kst() -> datetime:
    return datetime.now(_KST).replace(tzinfo=None)


# 보고서 - 일간은 거래일마다 1행, 주간은 주마다 1행
class TimelineReport(Base):
    __tablename__ = "timeline_report"

    # 같은 종류 + 같은 시작일은 한 행만 (반드시 튜플로 감쌀 것 - 끝의 콤마가 없으면 모델 로딩이 실패한다)
    __table_args__ = (UniqueConstraint("report_type", "start_date", name="uq_timeline_report_type_start"),)

    id: Mapped[int] = mapped_column(primary_key=True)

    # 보고서 종류 "DAILY" / "WEEKLY"
    report_type: Mapped[str] = mapped_column(String(10))

    # 기간 시작일. 일간은 그 거래일, 주간은 그 주 첫 거래일
    start_date: Mapped[date] = mapped_column(Date)

    # 기간 종료일. 일간은 start_date와 같고, 주간은 그 주 마지막 거래일
    end_date: Mapped[date] = mapped_column(Date)

    # 보고서 제목 (LLM)
    title: Mapped[str | None] = mapped_column(String(200), default=None)

    # 메인 한 줄 요약 (LLM). 메인 이미지 생성의 재료
    summary: Mapped[str | None] = mapped_column(String(300), default=None)

    # 메인 이미지 주소 (Supabase Storage 공개 URL)
    main_image_url: Mapped[str | None] = mapped_column(String(1000), default=None)

    # 결론 한 줄 요약 (LLM)
    conclusion: Mapped[str | None] = mapped_column(String(300), default=None)

    # 코스피 투자자별 순매수(백만원, 음수면 순매도). 주간은 그 주 일간 값의 합
    # 섹션2 카드에는 외국인만 쓰고, 기관·개인은 LLM 근거로 넘긴다
    foreign_net_buy: Mapped[int | None] = mapped_column(BigInteger, default=None)
    institution_net_buy: Mapped[int | None] = mapped_column(BigInteger, default=None)
    individual_net_buy: Mapped[int | None] = mapped_column(BigInteger, default=None)

    # VKOSPI 종가. 주간은 주 마지막 거래일 종가
    vkospi: Mapped[float | None] = mapped_column(Float, default=None)

    # VKOSPI 등락률(%). 일간은 전일 대비, 주간은 전주 대비
    vkospi_change_rate: Mapped[float | None] = mapped_column(Float, default=None)

    # 발행 시각 (한국 시간). LLM 문구까지 저장을 마친 시각이고, 그 전에는 NULL
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None)

    # 저장 시각 (한국 시간)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=_now_kst, server_default=_KST_NOW_SQL)

    # 자식 테이블 연결. seq 순서로 꺼내진다
    sections: Mapped[list["TimelineReportSection"]] = relationship(back_populates="report", cascade="all, delete-orphan", order_by="TimelineReportSection.seq")
    quarters: Mapped[list["TimelineReportQuarter"]] = relationship(back_populates="report", cascade="all, delete-orphan", order_by="TimelineReportQuarter.seq")
    sectors: Mapped[list["TimelineReportSector"]] = relationship(back_populates="report", cascade="all, delete-orphan", order_by="TimelineReportSector.seq")
    keywords: Mapped[list["TimelineReportKeyword"]] = relationship(back_populates="report", cascade="all, delete-orphan", order_by="TimelineReportKeyword.seq")
    terms: Mapped[list["TimelineReportTerm"]] = relationship(back_populates="report", cascade="all, delete-orphan", order_by="TimelineReportTerm.seq")


# 보고서 섹션 - 보고서당 3행 (1 핵심 이슈, 2 수급과 변동성, 3 주목할 섹터 - 주제는 prompts.REPORT_PROMPT에서 정한다)
class TimelineReportSection(Base):
    __tablename__ = "timeline_report_section"

    id: Mapped[int] = mapped_column(primary_key=True)

    # 소속 보고서
    report_id: Mapped[int] = mapped_column(ForeignKey("timeline_report.id", ondelete="CASCADE"))

    # 섹션 번호 (1, 2, 3)
    seq: Mapped[int] = mapped_column()

    # 섹션 타이틀 (LLM). 메인 화면의 섹션 타이틀 3개도 이 값을 쓴다
    title: Mapped[str | None] = mapped_column(String(200), default=None)

    # 섹션 설명 (LLM)
    description: Mapped[str | None] = mapped_column(Text, default=None)

    # 섹션 이미지 주소. 섹션1만 채우고 나머지는 NULL
    image_url: Mapped[str | None] = mapped_column(String(1000), default=None)

    # 저장 시각 (한국 시간)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=_now_kst, server_default=_KST_NOW_SQL)

    # 이 섹션의 핵심 요약 (section.points)
    points: Mapped[list["TimelineReportPoint"]] = relationship(back_populates="section", cascade="all, delete-orphan", order_by="TimelineReportPoint.seq")

    report: Mapped["TimelineReport"] = relationship(back_populates="sections")


# 섹션 핵심 요약 - 섹션당 3행
class TimelineReportPoint(Base):
    __tablename__ = "timeline_report_point"

    id: Mapped[int] = mapped_column(primary_key=True)

    # 소속 섹션
    section_id: Mapped[int] = mapped_column(ForeignKey("timeline_report_section.id", ondelete="CASCADE"))

    # 표시 순서 (1, 2, 3)
    seq: Mapped[int] = mapped_column()

    # 요약 문장 (LLM)
    body: Mapped[str] = mapped_column(Text)

    # 저장 시각 (한국 시간)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=_now_kst, server_default=_KST_NOW_SQL)

    section: Mapped["TimelineReportSection"] = relationship(back_populates="points")


# 섹션2 차트 분기 데이터 - 보고서당 6행 (현 분기 + 직전 5개, seq 1이 가장 오래된 분기)
class TimelineReportQuarter(Base):
    __tablename__ = "timeline_report_quarter"

    id: Mapped[int] = mapped_column(primary_key=True)

    # 소속 보고서
    report_id: Mapped[int] = mapped_column(ForeignKey("timeline_report.id", ondelete="CASCADE"))

    # 표시 순서 (1~6, 6이 현 분기)
    seq: Mapped[int] = mapped_column()

    # 차트 라벨 (예: "26/Q3")
    label: Mapped[str] = mapped_column(String(10))

    # 원/달러 환율. 분기 안 가장 늦은 달의 월간 값 (지난 분기는 분기 마지막 달, 현 분기는 이번 달까지 받은 최신 월)
    usd_krw: Mapped[float | None] = mapped_column(Float, default=None)

    # 분기 외국인 순매수 합계(백만원). 현 분기는 보고서 날짜까지의 합
    foreign_net_buy: Mapped[int | None] = mapped_column(BigInteger, default=None)

    # 현 분기면 True (차트에서 진행 중인 분기로 표시)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)

    # 저장 시각 (한국 시간)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=_now_kst, server_default=_KST_NOW_SQL)

    report: Mapped["TimelineReport"] = relationship(back_populates="quarters")


# 섹션3 주목할 섹터 카드 - 보고서당 3행
class TimelineReportSector(Base):
    __tablename__ = "timeline_report_sector"

    id: Mapped[int] = mapped_column(primary_key=True)

    # 소속 보고서
    report_id: Mapped[int] = mapped_column(ForeignKey("timeline_report.id", ondelete="CASCADE"))

    # 표시 순서 (1, 2, 3)
    seq: Mapped[int] = mapped_column()

    # 업종명 (예: "건설")
    sector_name: Mapped[str] = mapped_column(String(100))

    # 업종 등락률(%). 일간은 전일 대비, 주간은 전주 대비
    change_rate: Mapped[float | None] = mapped_column(Float, default=None)

    # 상승 종목 수 / 업종 전체 종목 수. 카드에 "업종 N개 중 M개 상승"과 비율로 표시한다
    # 주간은 API에 주간 값이 없어서 기준이 정해질 때까지 NULL일 수 있다
    rising_count: Mapped[int | None] = mapped_column(default=None)
    total_count: Mapped[int | None] = mapped_column(default=None)

    # 거래대금 / 비교 기간 거래대금(백만원). 일간은 당일·전일, 주간은 그 주·전주
    trade_amount: Mapped[int | None] = mapped_column(BigInteger, default=None)
    prev_trade_amount: Mapped[int | None] = mapped_column(BigInteger, default=None)

    # 저장 시각 (한국 시간)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=_now_kst, server_default=_KST_NOW_SQL)

    report: Mapped["TimelineReport"] = relationship(back_populates="sectors")


# 결론 키워드 - 보고서당 3행
class TimelineReportKeyword(Base):
    __tablename__ = "timeline_report_keyword"

    id: Mapped[int] = mapped_column(primary_key=True)

    # 소속 보고서
    report_id: Mapped[int] = mapped_column(ForeignKey("timeline_report.id", ondelete="CASCADE"))

    # 표시 순서 (1, 2, 3)
    seq: Mapped[int] = mapped_column()

    # 키워드 타이틀 (LLM)
    title: Mapped[str] = mapped_column(String(100))

    # 키워드 설명 (LLM)
    description: Mapped[str] = mapped_column(Text)

    # 저장 시각 (한국 시간)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=_now_kst, server_default=_KST_NOW_SQL)

    report: Mapped["TimelineReport"] = relationship(back_populates="keywords")


# 결론 어려운 용어 - 보고서당 3행
class TimelineReportTerm(Base):
    __tablename__ = "timeline_report_term"

    id: Mapped[int] = mapped_column(primary_key=True)

    # 소속 보고서
    report_id: Mapped[int] = mapped_column(ForeignKey("timeline_report.id", ondelete="CASCADE"))

    # 표시 순서 (1, 2, 3)
    seq: Mapped[int] = mapped_column()

    # 용어명 (예: "VKOSPI")
    term: Mapped[str] = mapped_column(String(100))

    # 용어 설명
    description: Mapped[str] = mapped_column(Text)

    # 설명 출처 "GLOSSARY"(glossary.py 사전) / "LLM"(사전에 없어 LLM이 작성 - 검토 후 사전에 정식 등록할 후보)
    source: Mapped[str] = mapped_column(String(10))

    # 저장 시각 (한국 시간)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=_now_kst, server_default=_KST_NOW_SQL)

    report: Mapped["TimelineReport"] = relationship(back_populates="terms")
