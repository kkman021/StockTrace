"""回測模組服務（規格 §12）。

買入價：訊號觸發日次日（T+1）開盤價。
回測沙盒參數獨立於 system_config。
"""
from datetime import date


def run_backtest_engine(
    start: date,
    end: date,
    breadth_thr: float,
    depth_thr: float,
    consec: int,
    holding_days: int,
    target_stocks: list[str] | None = None,
) -> int:
    """執行回測，回傳 backtest_run_id。"""
    raise NotImplementedError("TODO: scan signals in window, compute T+1 buy / T+1+holding sell, write backtest_results")


def aggregate_summary(run_id: int) -> list[dict]:
    """產出統計摘要表（規格 §12.4）。"""
    raise NotImplementedError("TODO: groupby stock_id, compute win_rate / avg_return / etc.")
