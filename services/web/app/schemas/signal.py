from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class SignalRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: date
    stock_id: str
    stock_name: str | None = None
    signal_type: str
    signal_tag: str
    breadth_score: Decimal | None = None
    depth_score: Decimal | None = None
    consecutive_days: int | None = None
    notified_at: datetime | None = None
    created_at: datetime
