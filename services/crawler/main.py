"""Crawler container entrypoint（規格 §22）。

- POST /crawl 接收 web 端的爬蟲請求
- 流程：crawler_mode='light' 時先試 httpx，validator fail → fallback playwright
       crawler_mode='playwright' 時直接走 playwright
- 對 aum_source='separate' 的 ETF，再抓 aum_url，由 parser.parse_aum_only 取數
"""
from __future__ import annotations

import logging
import time
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

from parsers import get_parser
from strategies.light import LightCrawler
from strategies.playwright import PlaywrightCrawler
from validator import validate

logger = logging.getLogger(__name__)


class CrawlRequest(BaseModel):
    etf_id: str
    disclosure_url: str
    aum_url: str | None = None
    aum_source: Literal["inline", "separate"] = "inline"
    crawler_mode: Literal["light", "playwright"] = "light"


class CrawlResponse(BaseModel):
    etf_id: str
    success: bool
    crawler_used: Literal["light", "playwright"] | None = None
    light_attempted: bool = False
    light_failed: bool = False
    records_count: int = 0
    holdings: list[dict] = []
    aum: int | None = None
    duration_ms: int = 0
    error: str | None = None


app = FastAPI(title="ETF Radar Crawler")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/crawl", response_model=CrawlResponse)
async def crawl(req: CrawlRequest) -> CrawlResponse:
    started = time.monotonic()
    parser = get_parser(req.etf_id)
    light_attempted = False
    light_failed = False
    error: str | None = None

    try:
        # Layer 1：light（除非明確指定 playwright）
        if req.crawler_mode == "light":
            light_attempted = True
            try:
                html = await LightCrawler().fetch(req.disclosure_url)
                parsed = parser.parse(html)
                result = validate(parsed.holdings, html)
                if result.is_valid:
                    aum = await _resolve_aum(parsed, req, parser, mode="light")
                    return CrawlResponse(
                        etf_id=req.etf_id,
                        success=True,
                        crawler_used="light",
                        light_attempted=True,
                        light_failed=False,
                        records_count=len(parsed.holdings),
                        holdings=parsed.holdings,
                        aum=aum,
                        duration_ms=_ms_since(started),
                    )
                light_failed = True
                logger.info("light parse invalid: %s", result.reason)
            except Exception as e:
                light_failed = True
                logger.info("light fetch failed: %s", e)

        # Layer 2：playwright fallback（或直接呼叫）
        html = await PlaywrightCrawler().fetch(req.disclosure_url)
        parsed = parser.parse(html)
        result = validate(parsed.holdings, html)
        if not result.is_valid:
            error = f"playwright_invalid: {result.reason}"
            return CrawlResponse(
                etf_id=req.etf_id,
                success=False,
                crawler_used="playwright",
                light_attempted=light_attempted,
                light_failed=light_failed,
                records_count=len(parsed.holdings),
                holdings=parsed.holdings,
                duration_ms=_ms_since(started),
                error=error,
            )

        aum = await _resolve_aum(parsed, req, parser, mode="playwright")
        return CrawlResponse(
            etf_id=req.etf_id,
            success=True,
            crawler_used="playwright",
            light_attempted=light_attempted,
            light_failed=light_failed,
            records_count=len(parsed.holdings),
            holdings=parsed.holdings,
            aum=aum,
            duration_ms=_ms_since(started),
        )

    except Exception as e:
        logger.exception("crawl failed: %s", req.etf_id)
        return CrawlResponse(
            etf_id=req.etf_id,
            success=False,
            light_attempted=light_attempted,
            light_failed=light_failed,
            duration_ms=_ms_since(started),
            error=str(e),
        )


async def _resolve_aum(parsed, req: CrawlRequest, parser, mode: str) -> int | None:
    """處理 aum_source='separate' 時的第二次抓取。"""
    if req.aum_source == "inline":
        return parsed.aum
    if not req.aum_url:
        return parsed.aum  # 設為 separate 但沒給 URL，當 inline 處理
    fetcher = LightCrawler() if mode == "light" else PlaywrightCrawler()
    try:
        aum_html = await fetcher.fetch(req.aum_url)
        return parser.parse_aum_only(aum_html) or parsed.aum
    except Exception as e:
        logger.info("aum_url fetch failed: %s", e)
        return parsed.aum


def _ms_since(started: float) -> int:
    return int((time.monotonic() - started) * 1000)
