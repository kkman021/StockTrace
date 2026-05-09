from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import ARRAY, BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BacktestRun(Base):
    __tablename__ = "backtest_runs"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    holding_days: Mapped[int] = mapped_column(Integer, nullable=False)
    breadth_threshold: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    depth_threshold: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    consecutive_days: Mapped[int] = mapped_column(Integer, nullable=False)
    target_stocks: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class BacktestResult(Base):
    __tablename__ = "backtest_results"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )
    run_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("backtest_runs.id"), nullable=False)
    stock_id: Mapped[str] = mapped_column(String(10), nullable=False)
    stock_name: Mapped[str | None] = mapped_column(String(100))
    trigger_date: Mapped[date] = mapped_column(Date, nullable=False)
    buy_date: Mapped[date] = mapped_column(Date, nullable=False)
    buy_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    sell_date: Mapped[date] = mapped_column(Date, nullable=False)
    sell_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    return_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    is_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    invalid_reason: Mapped[str | None] = mapped_column(String(100))
    breadth_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    depth_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    price_series: Mapped[Any | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
