"""分析任務（規格 §8、§9、§10、§21）。"""
from datetime import date

from celery_app import celery_app


@celery_app.task(name="tasks.analyze.analyze_consensus")
def analyze_consensus(target_date: str) -> dict:
    """計算 target_date 的加碼 + 減碼共識分數，寫入 consensus_scores。

    步驟：
    1. 取出 target_date 與 target_date-1 的 holding_records
    2. 對每檔 ETF 的每檔持股，跑三步驟主動加減碼計算
    3. 處理新建倉 / 清倉 / 除權息（spec §8.2）
    4. 跨 ETF 彙總，產出每檔股票的廣度 / 深度分數
    5. 計算連續加減碼天數（滑動窗口）
    6. 寫入 consensus_scores（同 date+stock_id 採 upsert）
    """
    raise NotImplementedError("TODO")


@celery_app.task(name="tasks.analyze.detect_signals")
def detect_signals(target_date: str) -> dict:
    """比對 system_config 門檻，決定 signal_tag / risk_tag，寫入 signal_records。

    僅針對「當日新觸發」的訊號寫入（避免重複）。
    """
    raise NotImplementedError("TODO")
