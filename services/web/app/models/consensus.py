from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Date, DateTime, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ConsensusScore(Base):
    __tablename__ = "consensus_scores"
    __table_args__ = (UniqueConstraint("date", "stock_id"),)

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    stock_id: Mapped[str] = mapped_column(String(10), nullable=False)
    stock_name: Mapped[str | None] = mapped_column(String(100))

    breadth_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    depth_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    accumulate_etf_count: Mapped[int | None] = mapped_column(Integer)
    total_amount: Mapped[int | None] = mapped_column(BigInteger)
    consecutive_days: Mapped[int | None] = mapped_column(Integer)
    signal_tag: Mapped[str | None] = mapped_column(String(20))

    reduction_breadth: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    reduction_etf_count: Mapped[int | None] = mapped_column(Integer)
    reduction_consec: Mapped[int | None] = mapped_column(Integer)
    risk_tag: Mapped[str | None] = mapped_column(String(20))

    param_breadth_thr: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    param_depth_thr: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    param_consec_days: Mapped[int | None] = mapped_column(Integer)
    param_red_breadth: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    param_red_consec: Mapped[int | None] = mapped_column(Integer)
    n_etfs: Mapped[int | None] = mapped_column(Integer)
    data_status: Mapped[str] = mapped_column(String(20), nullable=False, default="normal")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
