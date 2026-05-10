from datetime import date as _date
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CrawlLog, EtfList
from app.services import analyzer, crawler_client, signal_detector
from app.services.search import get_default_client as get_search_client

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


# ---------- 監控 ---------- #

@router.get("/crawl-status")
def crawl_status(
    target_date: date | None = Query(default=None, alias="date"),
    db: Session = Depends(get_db),
) -> dict:
    """每檔 ETF 的最新爬取結果（規格 §16 監控頁）。

    回傳 list 含：etf_id / etf_name / crawler_mode / fallback_count /
    last_log (status / crawler_used / records_count / duration_ms / error_message)
    """
    target = target_date or _date.today()

    etfs = db.execute(
        select(EtfList).where(EtfList.is_active.is_(True)).order_by(EtfList.etf_id)
    ).scalars().all()

    # 取每檔 ETF 在當日的最後一筆 crawl_log
    latest_subq = (
        select(CrawlLog.etf_id, func.max(CrawlLog.id).label("max_id"))
        .where(CrawlLog.crawl_date == target)
        .group_by(CrawlLog.etf_id)
        .subquery()
    )
    log_rows = db.execute(
        select(CrawlLog).join(latest_subq, CrawlLog.id == latest_subq.c.max_id)
    ).scalars().all()
    log_by_etf = {r.etf_id: r for r in log_rows}

    items = []
    for e in etfs:
        log = log_by_etf.get(e.etf_id)
        items.append({
            "etf_id": e.etf_id,
            "etf_name": e.etf_name,
            "crawler_mode": e.crawler_mode,
            "fallback_count": e.fallback_count,
            "last_success_date": e.last_success_date.isoformat() if e.last_success_date else None,
            "today_log": (
                {
                    "status": log.status,
                    "crawler_used": log.crawler_used,
                    "records_count": log.records_count,
                    "duration_ms": log.duration_ms,
                    "error_message": log.error_message,
                }
                if log
                else None
            ),
        })

    return {
        "date": target.isoformat(),
        "total": len(items),
        "success_today": sum(1 for x in items if x["today_log"] and x["today_log"]["status"] == "success"),
        "items": items,
    }


@router.get("/search-signals")
def search_signals(
    q: str | None = None,
    signal_type: str | None = None,
    signal_tag: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    size: int = 50,
) -> dict:
    """OpenSearch 全文 / 多維搜尋（規格 §11.3）。"""
    raw = get_search_client().search_signals(
        q=q, signal_type=signal_type, signal_tag=signal_tag,
        date_from=date_from, date_to=date_to, size=size,
    )
    hits = raw.get("hits", {})
    return {
        "total": hits.get("total", {}).get("value", 0),
        "items": [h.get("_source", {}) for h in hits.get("hits", [])],
    }
