# models > timeline.py
# 타임라인 콘텐츠 테이블
#
# [테이블 관계]
# timeline_slot 1 : N timeline_briefing_insight
# timeline_slot 1 : N timeline_beginner_guide
# timeline_slot 1 : N timeline_news
# timeline_slot 1 : N timeline_indicator          (07:30 슬롯만)
# timeline_slot 1 : N timeline_intraday_change    (15:30 슬롯만)
# timeline_slot 1 : N timeline_leading_sector
# timeline_leading_sector 1 : N timeline_leading_sector_stock
#
# [연결 원리]
# 데이터를 실제로 묶어주는 건 자식 테이블의 ForeignKey 컬럼(timeline_slot_id)이다.
# DB에는 이 숫자만 저장되고, relationship()은 그 연결을 코드에서 편하게 쓰기 위한 장치다
# (relationship을 다 지워도 DB 구조와 저장된 데이터는 동일하다).
#   - ForeignKey       : 실제 연결. 없으면 데이터가 안 묶임
#   - 부모 relationship : slot.insights 처럼 자식 목록을 바로 꺼내 씀
#   - 자식 relationship : insight.slot 처럼 부모를 거꾸로 찾아감
#   - back_populates   : 위 둘이 같은 관계의 양쪽 끝이라고 서로 지목해주는 값
#   - cascade          : 부모를 지우면 딸린 자식 행도 같이 지워지게 함 (파이썬 코드로 지울 때)
#   - ondelete=CASCADE : 같은 일을 DB가 직접 하게 함 (SQL로 지울 때)
#
# 둘을 같이 걸어둔 이유: cascade는 ORM으로 지울 때만(session.delete) 동작한다. Supabase 대시보드에서
# DELETE FROM timeline_slot 같은 SQL을 직접 실행하면 ORM을 거치지 않아서 FK 제약에 막힌다.
# DB에도 같이 걸어두면 어느 쪽으로 지워도 자식 행이 같이 정리된다

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base


# 타임라인 슬롯 - 하루에 8행이 쌓인다
class TimelineSlot(Base):
    # 실제 DB에 만들어질 테이블 이름
    __tablename__ = "timeline_slot"

    # 같은 날짜에 같은 시간대가 두 번 저장되는 것 방지(테이블 전체 설정)
    # 같은 날 같은 시간대가 두 번 저장되는 것을 DB에서 막는다
    # 주의: 반드시 튜플로 감싸야 한다(뒤에 콤마). 제약 하나만 쓸 때도 마찬가지다 -
    # 콤마가 없으면 모델을 읽는 순간 "__table_args__ value must be a tuple" 에러가 난다
    __table_args__ = (UniqueConstraint("trade_date", "time_slot", name="uq_timeline_slot_date_time"),)

    # 식별 번호
    id: Mapped[int] = mapped_column(primary_key=True)

    # 어느 거래일 데이터인지 (예: 2026-09-09)
    trade_date: Mapped[date] = mapped_column(Date)

    # 시간대 - 8개 고정 슬롯 중 하나: 07:30, 08:30, 09:30, 12:00, 14:00, 15:30, 17:30, 20:00
    time_slot: Mapped[str] = mapped_column(String(5))

    # LLM 브리핑 - 타이틀
    briefing_headline: Mapped[str | None] = mapped_column(String(200), default=None)

    # LLM 브리핑 - 부제
    briefing_subtitle: Mapped[str | None] = mapped_column(String(300), default=None)

    # 생성 일시
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # LLM 요약과 연결 (order_by - 꺼낼 때 seq 순서대로 정렬)
    insights: Mapped[list["TimelineBriefingInsight"]] = relationship(back_populates="slot", cascade="all, delete-orphan", order_by="TimelineBriefingInsight.seq")

    # 주린이 해설과 연결 (order_by - 꺼낼 때 seq 순서대로 정렬)
    beginner_guides: Mapped[list["TimelineBeginnerGuide"]] = relationship(back_populates="slot", cascade="all, delete-orphan", order_by="TimelineBeginnerGuide.seq")

    # 주요 뉴스와 연결
    news: Mapped[list["TimelineNews"]] = relationship(back_populates="slot", cascade="all, delete-orphan", order_by="TimelineNews.seq")

    # 어제 마감 & 글로벌 현황과 연결 (07:30 슬롯만)
    indicators: Mapped[list["TimelineIndicator"]] = relationship(back_populates="slot", cascade="all, delete-orphan")

    # 장중 변화와 연결 (15:30 슬롯만)
    intraday_changes: Mapped[list["TimelineIntradayChange"]] = relationship(back_populates="slot", cascade="all, delete-orphan")

    # 주도 섹터와 연결
    leading_sectors: Mapped[list["TimelineLeadingSector"]] = relationship(back_populates="slot", cascade="all, delete-orphan")


# LLM 요약 - 슬롯당 3행 (타이틀 + 설명)
class TimelineBriefingInsight(Base):
    __tablename__ = "timeline_briefing_insight"

    # 식별 번호
    id: Mapped[int] = mapped_column(primary_key=True)

    # 어느 슬롯에 속한 요약인지 - 실제 연결은 이 컬럼이 담당
    timeline_slot_id: Mapped[int] = mapped_column(ForeignKey("timeline_slot.id", ondelete="CASCADE"))

    # 표시 순서 (1, 2, 3)
    seq: Mapped[int] = mapped_column()

    # 요약 타이틀
    title: Mapped[str] = mapped_column(String(200))

    # 요약 설명
    body: Mapped[str] = mapped_column(Text)

    # 역방향 연결
    slot: Mapped["TimelineSlot"] = relationship(back_populates="insights")


# 주린이 해설 - 슬롯당 3행 (타이틀 + 내용 + 태그)
class TimelineBeginnerGuide(Base):
    __tablename__ = "timeline_beginner_guide"

    # 식별 번호
    id: Mapped[int] = mapped_column(primary_key=True)

    # 어느 슬롯에 속한 해설인지 - 실제 연결은 이 컬럼이 담당
    timeline_slot_id: Mapped[int] = mapped_column(ForeignKey("timeline_slot.id", ondelete="CASCADE"))

    # 표시 순서 (1, 2, 3)
    seq: Mapped[int] = mapped_column()

    # 해설 타이틀 (예: "왜 올랐을까요?")
    title: Mapped[str] = mapped_column(String(200))

    # 해설 내용
    body: Mapped[str] = mapped_column(Text)

    # 태그 - 쉼표로 구분해서 한 칸에 저장 (예: "금리인하, 유동성공급")
    tags: Mapped[str | None] = mapped_column(String(200), default=None)

    # 역방향 연결
    slot: Mapped["TimelineSlot"] = relationship(back_populates="beginner_guides")


# 주요 뉴스 - 슬롯당 여러 건 (출처는 네이버 고정)
class TimelineNews(Base):
    __tablename__ = "timeline_news"

    # 식별 번호
    id: Mapped[int] = mapped_column(primary_key=True)

    # 어느 슬롯에 속한 뉴스인지 - 실제 연결은 이 컬럼이 담당
    timeline_slot_id: Mapped[int] = mapped_column(ForeignKey("timeline_slot.id", ondelete="CASCADE"))

    # 화면에 뿌릴 순서 (1부터). 중요도가 높은 기사가 1번이다 (다른 테이블의 seq와 시작 번호를 맞춤)
    # DB는 ORDER BY 없이 조회하면 행 순서를 보장하지 않는다. 이 컬럼이 없으면 애써 정한
    # 중요도 순서가 조회할 때마다 뒤섞인다
    seq: Mapped[int] = mapped_column(default=1)

    # 뉴스 타이틀
    title: Mapped[str] = mapped_column(String(500))

    # 뉴스 설명
    summary: Mapped[str | None] = mapped_column(Text, default=None)

    # 기사 링크
    url: Mapped[str] = mapped_column(String(1000))

    # 역방향 연결
    slot: Mapped["TimelineSlot"] = relationship(back_populates="news")


# 어제 마감 & 글로벌 현황 - 07:30 슬롯에만 6행
# (코스피, 코스닥, 나스닥, S&P500, 니케이, 환율)
class TimelineIndicator(Base):
    __tablename__ = "timeline_indicator"

    # 식별 번호
    id: Mapped[int] = mapped_column(primary_key=True)

    # 어느 슬롯에 속한 지표인지 - 실제 연결은 이 컬럼이 담당
    timeline_slot_id: Mapped[int] = mapped_column(ForeignKey("timeline_slot.id", ondelete="CASCADE"))

    # 지표 명칭 (예: "KOSPI")
    name: Mapped[str] = mapped_column(String(50))

    # 가격
    price: Mapped[float] = mapped_column(Float)

    # 등락폭(%)
    change_rate: Mapped[float] = mapped_column(Float)

    # 역방향 연결
    slot: Mapped["TimelineSlot"] = relationship(back_populates="indicators")


# 장중 변화 - 15:30 슬롯에만 3행 (코스피, 코스닥, 환율)
class TimelineIntradayChange(Base):
    __tablename__ = "timeline_intraday_change"

    # 식별 번호
    id: Mapped[int] = mapped_column(primary_key=True)

    # 어느 슬롯에 속한 값인지 - 실제 연결은 이 컬럼이 담당
    timeline_slot_id: Mapped[int] = mapped_column(ForeignKey("timeline_slot.id", ondelete="CASCADE"))

    # 지표 명칭 (예: "KOSPI")
    name: Mapped[str] = mapped_column(String(50))

    # 07:30 가격
    morning_price: Mapped[float] = mapped_column(Float)

    # 15:30 가격
    closing_price: Mapped[float] = mapped_column(Float)

    # 07:30 대비 변동폭(%)
    change_rate: Mapped[float] = mapped_column(Float)

    # 역방향 연결
    slot: Mapped["TimelineSlot"] = relationship(back_populates="intraday_changes")


# 주도 섹터 - 슬롯당 3행 (업종 등락률 TOP3)
class TimelineLeadingSector(Base):
    __tablename__ = "timeline_leading_sector"

    # 식별 번호
    id: Mapped[int] = mapped_column(primary_key=True)

    # 어느 슬롯에 속한 섹터인지 - 실제 연결은 이 컬럼이 담당
    timeline_slot_id: Mapped[int] = mapped_column(ForeignKey("timeline_slot.id", ondelete="CASCADE"))

    # 섹터명 (예: "화학")
    name: Mapped[str] = mapped_column(String(100))

    # 섹터 상승률(%)
    change_rate: Mapped[float] = mapped_column(Float)

    # 이 섹터의 대표 종목 목록 - 코드에서는 sector.stocks 로 접근
    stocks: Mapped[list["TimelineLeadingSectorStock"]] = relationship(back_populates="sector", cascade="all, delete-orphan")

    # 역방향 연결
    slot: Mapped["TimelineSlot"] = relationship(back_populates="leading_sectors")


# 섹터별 대표 종목 - 섹터당 1~2행
# 상승 1위와 거래대금 1위가 같은 종목이면 1행("상승·거래 1위"), 다르면 2행으로 저장
class TimelineLeadingSectorStock(Base):
    __tablename__ = "timeline_leading_sector_stock"

    # 식별 번호
    id: Mapped[int] = mapped_column(primary_key=True)

    # 어느 섹터에 속한 종목인지 - 실제 연결은 이 컬럼이 담당
    sector_id: Mapped[int] = mapped_column(ForeignKey("timeline_leading_sector.id", ondelete="CASCADE"))

    # 종목명 (예: "롯데케미칼")
    name: Mapped[str] = mapped_column(String(100))

    # 종목 등락률(%)
    change_rate: Mapped[float] = mapped_column(Float)

    # 라벨 - "상승 1위", "거래대금 1위", "상승·거래 1위"
    label: Mapped[str] = mapped_column(String(30))

    # 역방향 연결
    sector: Mapped["TimelineLeadingSector"] = relationship(back_populates="stocks")
