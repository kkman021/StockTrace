from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class HoldingRecord(Base):
    __tablename__ = "holding_records"
    __table_args__ = (UniqueConstraint("etf_id", "date", "stock_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    etf_id: Mapped[str] = mapped_column(String(10), ForeignKey("etf_list.etf_id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    stock_id: Mapped[str] = mapped_column(String(10), nullable=False)
    shares_held: Mapped[int] = mapped_column(BigInteger, nullable=False)
    weight_pct: Mapped[Decimal | None] = mapped_column(Numeric(6, 4))
    aum: Mapped[int | None] = mapped_column(BigInteger)
    aum_source: Mapped[str | None] = mapped_column(String(20))
    is_new_position: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    data_status: Mapped[str] = mapped_column(String(20), nullable=False, default="normal")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
