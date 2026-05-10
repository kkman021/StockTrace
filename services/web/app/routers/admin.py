from datetime import date as _date
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import analyzer, crawler_client, signal_detector

router = APIRouter()


@router.post("/crawl")
async def trigger_full_crawl(
    target_date: date | None = Query(default=None, alias="date"),
    retry_missing_only: bool = False,
    db: Session = Depends(get_db),
) -> dict:
    """全量爬取所有啟用中的 ETF（規格 §14、§21）。"""
    target = target_date or _date.today()
    return await crawler_client.crawl_all(db, target, retry_missing_only=retry_missing_only)


@router.post("/crawl/{etf_id}")
async def trigger_single_crawl(
    etf_id: str,
    target_date: date | None = Query(default=None, alias="date"),
    db: Session = Depends(get_db),
) -> dict:
    target = target_date or _date.today()
    outcome = await crawler_client.crawl_single(db, etf_id, target)
    return {
        "etf_id": outcome.etf_id,
        "success": outcome.success,
        "crawler_used": outcome.crawler_used,
        "records_count": outcome.records_count,
        "aum_source": outcome.aum_source,
        "fallback_count": outcome.fallback_count,
        "crawler_mode_after": outcome.crawler_mode_after,
        "error": outcome.error,
    }


@router.post("/analyze/{target_date}")
def trigger_analyze(target_date: date, db: Session = Depends(get_db)) -> dict:
    """讀取 target_date 與 target_date-1 的持股 → 跨 ETF 彙總 → 寫入 consensus_scores。"""
    return analyzer.analyze_date(db, target_date)


@router.post("/detect-signals/{target_date}")
def trigger_detect_signals(target_date: date, db: Session = Depends(get_db)) -> dict:
    """掃描 target_date 的 consensus_scores，將新觸發的訊號寫入 signal_records。"""
    return signal_detector.detect_date(db, target_date)
