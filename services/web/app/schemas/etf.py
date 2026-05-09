from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict


class EtfBase(BaseModel):
    etf_id: str
    etf_name: str
    issuer: str
    disclosure_url: str
    aum_url: str | None = None
    aum_source: Literal["inline", "separate"] = "inline"
    crawler_mode: Literal["light", "playwright"] = "light"
    is_active: bool = True
    notes: str | None = None


class EtfCreate(EtfBase):
    pass


class EtfUpdate(BaseModel):
    etf_name: str | None = None
    disclosure_url: str | None = None
    aum_url: str | None = None
    aum_source: Literal["inline", "separate"] | None = None
    crawler_mode: Literal["light", "playwright"] | None = None
    is_active: bool | None = None
    notes: str | None = None


class EtfRead(EtfBase):
    model_config = ConfigDict(from_attributes=True)

    fallback_count: int
    added_date: date
    last_success_date: date | None = None
    last_known_aum: int | None = None


class AumOverride(BaseModel):
    aum: int
