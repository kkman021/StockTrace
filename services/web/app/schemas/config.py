from pydantic import BaseModel, Field


class ThresholdConfig(BaseModel):
    breadth_threshold: float = Field(ge=0.1, le=0.9)
    depth_threshold: float = Field(ge=0.1, le=0.9)
    consecutive_days: int = Field(ge=1, le=10)
    sliding_window: int = Field(ge=3, le=20)
    reduction_breadth_threshold: float = Field(ge=0.1, le=0.9)
    reduction_consecutive_days: int = Field(ge=1, le=10)


class ThresholdConfigPatch(BaseModel):
    breadth_threshold: float | None = Field(default=None, ge=0.1, le=0.9)
    depth_threshold: float | None = Field(default=None, ge=0.1, le=0.9)
    consecutive_days: int | None = Field(default=None, ge=1, le=10)
    sliding_window: int | None = Field(default=None, ge=3, le=20)
    reduction_breadth_threshold: float | None = Field(default=None, ge=0.1, le=0.9)
    reduction_consecutive_days: int | None = Field(default=None, ge=1, le=10)
