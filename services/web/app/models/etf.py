from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EtfList(Base):
    __tablename__ = "etf_list"

    etf_id: Mapped[str] = mapped_column(String(10), primary_key=True)
    etf_name: Mapped[str] = mapped_column(String(100), nullable=False)
    issuer: Mapped[str] = mapped_column(String(100), nullable=False)
    disclosure_url: Mapped[str] = mapped_column(Text, nullable=False)
    aum_url: Mapped[str | None] = mapped_column(Text)
    aum_source: Mapped[str] = mapped_column(String(10), nullable=False, default="inline")
    crawler_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="light")
    fallback_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    added_date: Mapped[date] = mapped_column(Date, nullable=False, server_default=func.current_date())
    last_success_date: Mapped[date | None] = mapped_column(Date)
    last_known_aum: Mapped[int | None] = mapped_column(BigInteger)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
