"""爬蟲任務（規格 §6、§14、§21）。

Worker 是排程器；實際抓取邏輯由 web container 的 /api/admin/crawl 端點統一處理，
避免在 worker 中重複維護 ORM、AUM 三層備援、fallback_count 升級等狀態機。
"""
import os
from datetime import date as _date

import httpx

from celery_app import celery_app


WEB_URL = os.environ.get("WEB_URL", "http://web:8000")
HTTP_TIMEOUT = 600.0  # 全量爬取可能耗時，給 10 分鐘上限


@celery_app.task(name="tasks.crawl.crawl_single_etf")
def crawl_single_etf(etf_id: str, target_date: str | None = None) -> dict:
    """單一 ETF 爬取（手動觸發或排程補抓用）。"""
    target = target_date or _date.today().isoformat()
    resp = httpx.post(
        f"{WEB_URL}/api/admin/crawl/{etf_id}",
        params={"date": target},
        timeout=HTTP_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


@celery_app.task(name="tasks.crawl.crawl_all_etfs")
def crawl_all_etfs(
    target_date: str | None = None,
    retry_missing_only: bool = False,
) -> dict:
    """全量爬取（規格 §14：18:30/19:30/21:00 排程觸發）。

    19:30 與 21:00 由 Beat 設定 retry_missing_only=True，僅補抓尚未成功的 ETF。
    """
    target = target_date or _date.today().isoformat()
    resp = httpx.post(
        f"{WEB_URL}/api/admin/crawl",
        params={"date": target, "retry_missing_only": str(retry_missing_only).lower()},
        timeout=HTTP_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()
