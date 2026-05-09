"""分析任務（規格 §8、§9、§10、§21）。

Worker 是排程器，實際分析邏輯在 web container 的 /api/admin/analyze/{date}
與 /api/admin/detect-signals/{date}（避免 worker / web 重複維護同一份計算與 ORM）。
"""
import os
from datetime import date as _date

import httpx

from celery_app import celery_app


WEB_URL = os.environ.get("WEB_URL", "http://web:8000")
HTTP_TIMEOUT = 60.0


@celery_app.task(name="tasks.analyze.analyze_consensus")
def analyze_consensus(target_date: str | None = None) -> dict:
    """呼叫 web 的 analyze 端點計算共識分數（規格 §8）。"""
    target_date = target_date or _date.today().isoformat()
    resp = httpx.post(f"{WEB_URL}/api/admin/analyze/{target_date}", timeout=HTTP_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


@celery_app.task(name="tasks.analyze.detect_signals")
def detect_signals(target_date: str | None = None) -> dict:
    """呼叫 web 的 detect-signals 端點寫入 signal_records（規格 §13.3）。"""
    target_date = target_date or _date.today().isoformat()
    resp = httpx.post(f"{WEB_URL}/api/admin/detect-signals/{target_date}", timeout=HTTP_TIMEOUT)
    resp.raise_for_status()
    return resp.json()
