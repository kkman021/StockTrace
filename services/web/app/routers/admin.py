from datetime import date

from fastapi import APIRouter

router = APIRouter()


@router.post("/crawl", status_code=202)
def trigger_full_crawl():
    """手動觸發全量爬蟲（呼叫 worker 的 crawl_all_etfs）。"""
    raise NotImplementedError("TODO: dispatch celery task crawl_all_etfs")


@router.post("/crawl/{etf_id}", status_code=202)
def trigger_single_crawl(etf_id: str):
    raise NotImplementedError("TODO: dispatch crawl_single_etf")


@router.post("/analyze/{target_date}", status_code=202)
def trigger_analyze(target_date: date):
    """手動重跑分析。"""
    raise NotImplementedError("TODO: dispatch analyze_consensus + detect_signals")
