"""Crawler client（規格 §6、§7、§22）。

職責:
- 呼叫 crawler container 的 /crawl 端點
- AUM 三層備援（規格 §6.4）
- 連續 fallback_count 自動升級（規格 §6.3）
- 寫入 holding_records 與 crawl_logs

刻意設計成可注入 fetch callable，方便 mock 測試。
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Awaitable, Callable

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models import CrawlLog, EtfList, HoldingRecord

logger = logging.getLogger(__name__)


CRAWLER_URL = os.environ.get("CRAWLER_URL", "http://crawler:8001")
FALLBACK_UPGRADE_THRESHOLD = 5  # 規格 §6.3：連續 5 次升級

# AUM 來源標籤（寫入 holding_records.aum_source）
AUM_SOURCE_CRAWLED = "crawled"
AUM_SOURCE_PREVIOUS = "previous_day"
AUM_SOURCE_MANUAL = "manual"
AUM_SOURCE_MISSING = "missing"


@dataclass
class CrawlOutcome:
    etf_id: str
    success: bool
    crawler_used: str | None = None
    records_count: int = 0
    aum_source: str | None = None
    fallback_count: int = 0
    crawler_mode_after: str | None = None
    error: str | None = None


# 預設 fetch 實作；測試可注入 stub
async def default_fetch(payload: dict) -> dict:
    timeout = httpx.Timeout(60.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(f"{CRAWLER_URL}/crawl", json=payload)
        resp.raise_for_status()
        return resp.json()


def _resolve_aum(
    db: Session,
    etf: EtfList,
    target_date: date,
    crawled_aum: int | None,
) -> tuple[int | None, str]:
    """三層備援（規格 §6.4）。"""
    if crawled_aum:
        return crawled_aum, AUM_SOURCE_CRAWLED

    # 第一備援：前一個交易日的 AUM（從 holding_records 找最近一筆）
    prior = db.execute(
        select(HoldingRecord.aum)
        .where(
            HoldingRecord.etf_id == etf.etf_id,
            HoldingRecord.date < target_date,
            HoldingRecord.aum.is_not(None),
        )
        .order_by(HoldingRecord.date.desc())
        .limit(1)
    ).scalar_one_or_none()
    if prior:
        return int(prior), AUM_SOURCE_PREVIOUS

    # 第二備援：管理介面手動輸入
    if etf.last_known_aum:
        return int(etf.last_known_aum), AUM_SOURCE_MANUAL

    return None, AUM_SOURCE_MISSING


def _write_holdings(
    db: Session,
    etf_id: str,
    target_date: date,
    holdings: list[dict],
    aum: int | None,
    aum_source: str,
) -> None:
    """以 (etf_id, date, stock_id) upsert holding_records。"""
    yesterday_ids = set(
        db.execute(
            select(HoldingRecord.stock_id).where(
                HoldingRecord.etf_id == etf_id,
                HoldingRecord.date == target_date - timedelta(days=1),
            )
        ).scalars()
    )

    for h in holdings:
        stock_id = h["stock_id"]
        is_new = stock_id not in yesterday_ids
        weight_pct = h.get("weight_pct")
        stmt = pg_insert(HoldingRecord).values(
            etf_id=etf_id,
            date=target_date,
            stock_id=stock_id,
            shares_held=h["shares_held"],
            weight_pct=Decimal(str(weight_pct)) if weight_pct is not None else None,
            aum=aum,
            aum_source=aum_source,
            is_new_position=is_new,
            data_status="aum_missing" if aum_source == AUM_SOURCE_MISSING else "normal",
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["etf_id", "date", "stock_id"],
            set_={
                "shares_held": stmt.excluded.shares_held,
                "weight_pct": stmt.excluded.weight_pct,
                "aum": stmt.excluded.aum,
                "aum_source": stmt.excluded.aum_source,
                "is_new_position": stmt.excluded.is_new_position,
                "data_status": stmt.excluded.data_status,
            },
        )
        db.execute(stmt)


def _update_crawler_state(
    etf: EtfList,
    target_date: date,
    response: dict,
) -> None:
    """根據爬蟲回應更新 fallback_count 與 crawler_mode（規格 §6.3）。

    規則：
    - 成功 + 用 light → 重置 fallback_count = 0
    - 成功但 light_failed (升 playwright 才成功) → fallback_count += 1
      累計達 5 → crawler_mode = 'playwright'
    - 失敗 → 不動 fallback_count（避免重複計數）；但 last_success_date 不更新
    """
    if not response.get("success"):
        return

    if response.get("light_failed"):
        etf.fallback_count = (etf.fallback_count or 0) + 1
        if etf.fallback_count >= FALLBACK_UPGRADE_THRESHOLD:
            etf.crawler_mode = "playwright"
    elif response.get("crawler_used") == "light":
        etf.fallback_count = 0

    etf.last_success_date = target_date


def _log_crawl(
    db: Session,
    etf_id: str,
    target_date: date,
    response: dict,
) -> None:
    db.add(
        CrawlLog(
            etf_id=etf_id,
            crawl_date=target_date,
            crawler_used=response.get("crawler_used"),
            status="success" if response.get("success") else "failed",
            records_count=response.get("records_count") or 0,
            duration_ms=response.get("duration_ms"),
            error_message=response.get("error"),
        )
    )


async def crawl_single(
    db: Session,
    etf_id: str,
    target_date: date,
    fetch: Callable[[dict], Awaitable[dict]] | None = None,
) -> CrawlOutcome:
    """單一 ETF 完整爬取流程。"""
    etf = db.get(EtfList, etf_id)
    if etf is None:
        return CrawlOutcome(etf_id=etf_id, success=False, error="etf_not_found")
    if not etf.is_active:
        return CrawlOutcome(etf_id=etf_id, success=False, error="etf_inactive")

    fetcher = fetch or default_fetch
    payload = {
        "etf_id": etf.etf_id,
        "disclosure_url": etf.disclosure_url,
        "aum_url": etf.aum_url,
        "aum_source": etf.aum_source,
        "crawler_mode": etf.crawler_mode,
    }

    try:
        response = await fetcher(payload)
    except Exception as e:
        logger.exception("crawler call failed: %s", etf_id)
        _log_crawl(db, etf_id, target_date, {"success": False, "error": str(e)})
        db.commit()
        return CrawlOutcome(etf_id=etf_id, success=False, error=str(e))

    _log_crawl(db, etf_id, target_date, response)

    if response.get("success") and response.get("holdings"):
        crawled_aum = response.get("aum")
        aum, aum_source = _resolve_aum(db, etf, target_date, crawled_aum)
        _write_holdings(db, etf_id, target_date, response["holdings"], aum, aum_source)
        _update_crawler_state(etf, target_date, response)
        db.commit()
        return CrawlOutcome(
            etf_id=etf_id,
            success=True,
            crawler_used=response.get("crawler_used"),
            records_count=response.get("records_count") or 0,
            aum_source=aum_source,
            fallback_count=etf.fallback_count,
            crawler_mode_after=etf.crawler_mode,
        )

    db.commit()
    return CrawlOutcome(
        etf_id=etf_id,
        success=False,
        crawler_used=response.get("crawler_used"),
        error=response.get("error"),
    )


async def crawl_all(
    db: Session,
    target_date: date,
    retry_missing_only: bool = False,
    fetch: Callable[[dict], Awaitable[dict]] | None = None,
) -> dict:
    """全量爬取所有啟用中的 ETF（規格 §14：18:30/19:30/21:00 排程）。

    retry_missing_only=True 時，僅補抓今日尚未成功的 ETF（19:30 / 21:00 用）。
    """
    active_etfs = db.execute(
        select(EtfList).where(EtfList.is_active.is_(True))
    ).scalars().all()

    if retry_missing_only:
        already_done = set(
            db.execute(
                select(HoldingRecord.etf_id)
                .where(HoldingRecord.date == target_date)
                .distinct()
            ).scalars()
        )
        active_etfs = [e for e in active_etfs if e.etf_id not in already_done]

    outcomes: list[CrawlOutcome] = []
    for etf in active_etfs:
        outcome = await crawl_single(db, etf.etf_id, target_date, fetch=fetch)
        outcomes.append(outcome)

    return {
        "date": str(target_date),
        "attempted": len(outcomes),
        "success": sum(1 for o in outcomes if o.success),
        "failed": sum(1 for o in outcomes if not o.success),
        "outcomes": [
            {
                "etf_id": o.etf_id,
                "success": o.success,
                "crawler_used": o.crawler_used,
                "records_count": o.records_count,
                "aum_source": o.aum_source,
                "fallback_count": o.fallback_count,
                "crawler_mode_after": o.crawler_mode_after,
                "error": o.error,
            }
            for o in outcomes
        ],
    }
