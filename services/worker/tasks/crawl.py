"""爬蟲任務（規格 §6、§21）。

呼叫 crawler container 的 HTTP API，將結果寫入 holding_records / crawl_logs，
並維護 etf_list.fallback_count 與 crawler_mode 自動升級邏輯。
"""
from datetime import date

from celery_app import celery_app


@celery_app.task(name="tasks.crawl.crawl_single_etf")
def crawl_single_etf(etf_id: str, target_date: str | None = None) -> dict:
    """爬取單一 ETF。
    1. 從 etf_list 讀取 disclosure_url / aum_url / crawler_mode
    2. POST 到 crawler:8001/crawl
    3. 驗證結果（spec §6.2 失敗判定）
    4. 更新 fallback_count（連續 5 次升級成 playwright）
    5. 寫入 holding_records 與 crawl_logs
    6. AUM 三層備援（spec §6.4）
    """
    raise NotImplementedError("TODO")


@celery_app.task(name="tasks.crawl.crawl_all_etfs")
def crawl_all_etfs(target_date: str | None = None, retry_missing_only: bool = False) -> dict:
    """並行觸發所有 is_active=True 的 ETF 爬蟲。"""
    raise NotImplementedError("TODO: fan-out crawl_single_etf via group()")
