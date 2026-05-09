from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class BacktestCreate(BaseModel):
    start_date: date
    end_date: date
    holding_days: int = Field(ge=1, le=60)
    breadth_threshold: float = Field(ge=0.1, le=0.9)
    depth_threshold: float = Field(ge=0.1, le=0.9)
    consecutive_days: int = Field(ge=1, le=10)
    target_stocks: list[str] | None = None


class BacktestRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    start_date: date
    end_date: date
    holding_days: int
    breadth_threshold: Decimal
    depth_threshold: Decimal
    consecutive_days: int
    target_stocks: list[str] | None = None
    status: str


class BacktestSummaryRow(BaseModel):
    stock_id: str
    stock_name: str | None = None
    trigger_count: int
    win_rate: float
    avg_return: float
    max_return: float
    min_return: float
    avg_breadth: float
    avg_depth: float
