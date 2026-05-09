from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

from strategies.light import LightCrawler
from strategies.playwright import PlaywrightCrawler
from validator import validate_holding_records


class CrawlRequest(BaseModel):
    etf_id: str
    disclosure_url: str
    aum_url: str | None = None
    aum_source: Literal["inline", "separate"] = "inline"
    crawler_mode: Literal["light", "playwright"] = "light"


class CrawlResponse(BaseModel):
    etf_id: str
    crawler_used: Literal["light", "playwright"]
    success: bool
    records_count: int
    holdings: list[dict]
    aum: int | None = None
    error: str | None = None


app = FastAPI(title="ETF Radar Crawler")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/crawl", response_model=CrawlResponse)
async def crawl(req: CrawlRequest) -> CrawlResponse:
    """執行單一 ETF 爬取（規格 §22）。

    若 crawler_mode='playwright'，直接走 Layer 2。
    否則先走 Layer 1，驗證失敗再 fallback。
    """
    raise NotImplementedError(
        "TODO: orchestrate Light → validate → Playwright fallback flow"
    )
