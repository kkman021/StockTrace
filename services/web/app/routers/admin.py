from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import analyzer, signal_detector

router = APIRouter()


@router.post("/crawl", status_code=202)
def trigger_full_crawl():
    """手動觸發全量爬蟲（呼叫 worker 的 crawl_all_etfs）。"""
    raise NotImplementedError("TODO: dispatch celery task crawl_all_etfs")


@router.post("/crawl/{etf_id}", status_code=202)
def trigger_single_crawl(etf_id: str):
    raise NotImplementedError("TODO: dispatch crawl_single_etf")


@router.post("/analyze/{target_date}")
def trigger_analyze(target_date: date, db: Session = Depends(get_db)) -> dict:
    """讀取 target_date 與 target_date-1 的持股 → 跨 ETF 彙總 → 寫入 consensus_scores。"""
    return analyzer.analyze_date(db, target_date)


@router.post("/detect-signals/{target_date}")
def trigger_detect_signals(target_date: date, db: Session = Depends(get_db)) -> dict:
    """掃描 target_date 的 consensus_scores，將新觸發的訊號寫入 signal_records。"""
    return signal_detector.detect_date(db, target_date)
