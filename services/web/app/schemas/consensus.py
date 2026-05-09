from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ConsensusRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date
    stock_id: str
    stock_name: str | None = None
    breadth_score: Decimal | None = None
    depth_score: Decimal | None = None
    accumulate_etf_count: int | None = None
    total_amount: int | None = None
    consecutive_days: int | None = None
    signal_tag: str | None = None


class ReductionRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date
    stock_id: str
    stock_name: str | None = None
    reduction_breadth: Decimal | None = None
    reduction_etf_count: int | None = None
    reduction_consec: int | None = None
    risk_tag: str | None = None
