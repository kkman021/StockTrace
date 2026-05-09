from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Date, DateTime, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SignalRecord(Base):
    __tablename__ = "signal_records"
    __table_args__ = (UniqueConstraint("date", "stock_id", "signal_type"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    stock_id: Mapped[str] = mapped_column(String(10), nullable=False)
    stock_name: Mapped[str | None] = mapped_column(String(100))
    signal_type: Mapped[str] = mapped_column(String(20), nullable=False)
    signal_tag: Mapped[str] = mapped_column(String(20), nullable=False)
    breadth_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    depth_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    consecutive_days: Mapped[int | None] = mapped_column(Integer)
    notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
