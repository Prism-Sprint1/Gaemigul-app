# 원/달러 환율 30분 스냅샷. 오늘·5일 차트의 실제 관측값을 보존한다.

from datetime import datetime

from sqlalchemy import DateTime, Float, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.database import Base


class ExchangeRateSnapshot(Base):
    __tablename__ = "market_exchange_rate_snapshot"
    __table_args__ = (UniqueConstraint("sampled_at", name="uq_market_exchange_rate_sampled_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    sampled_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), index=True)
    value: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False))
