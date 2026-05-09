"""回測任務（規格 §12、§21）。"""
from celery_app import celery_app


@celery_app.task(name="tasks.backtest.run_backtest")
def run_backtest(run_id: int) -> dict:
    """執行回測：
    1. 讀取 backtest_runs[run_id] 的參數
    2. 在指定區間掃描所有日子，套用獨立門檻找出觸發訊號
    3. 對每個觸發點記錄 T+1 開盤買 / T+1+holding_days 開盤賣
    4. 計算 return_rate，寫入 backtest_results
    5. 將 backtest_runs.status 更新為 completed
    """
    raise NotImplementedError("TODO")
