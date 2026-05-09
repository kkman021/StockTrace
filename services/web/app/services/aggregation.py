"""跨 ETF 共識彙總（純函數，規格 §8、§9、§10）。

把多個 ETF 的單檔股票活動結果聚合成股票層級的廣度 / 深度分數。
"""
from dataclasses import dataclass, field
from decimal import Decimal

from app.services.consensus import (
    ActivityResult,
    breadth_score,
    classify_score,
    compute_active_shares,
    depth_score,
)
from app.services.reduction import reduction_breadth_score


@dataclass
class HoldingDelta:
    """單一 ETF × 單一持股的計算輸入。

    若 yesterday_shares=0 則代表今日新建倉；today_shares=0 代表今日清倉。
    """

    etf_id: str
    stock_id: str
    yesterday_shares: int = 0
    today_shares: int = 0
    stock_dividend_ratio: Decimal = field(default_factory=lambda: Decimal("0"))
    aum_today: int | None = None
    aum_yesterday: int | None = None
    close_price: Decimal = field(default_factory=lambda: Decimal("0"))


@dataclass
class StockConsensus:
    """單一股票經跨 ETF 彙總後的共識指標（不含 consecutive_days）。

    consecutive_days 須由 DB 端依歷史 consensus_scores 計算，於 analyzer 層補上。
    """

    stock_id: str
    n_etfs: int
    accumulate_etf_count: int
    reduction_etf_count: int
    breadth_score: float
    depth_score: float
    reduction_breadth: float
    total_active_amount: int
    signal_tag: str | None  # 規格 §9.2 矩陣分類（不含 consec）


def aggregate(
    deltas: list[HoldingDelta],
    n_etfs: int,
    total_aum: int,
    breadth_thr: float,
    depth_thr: float,
) -> list[StockConsensus]:
    """跨 ETF 彙總（規格 §8.1）。

    Args:
        deltas: 所有 (ETF, 股票) 配對的 delta，包含今日新建倉與昨日清倉。
        n_etfs: 當日 is_active=true AND 爬蟲成功的 ETF 數量（規格 §7.3）。
        total_aum: N 檔 ETF 今日 AUM 總和（含 AUM 缺值的 ETF 應排除於分母外）。
        breadth_thr / depth_thr: 用於 signal_tag 矩陣分類（規格 §9.2）。

    Returns:
        每檔股票一筆 StockConsensus。
    """
    by_stock: dict[str, list[ActivityResult]] = {}
    for delta in deltas:
        result = compute_active_shares(
            yesterday_shares=delta.yesterday_shares,
            today_shares=delta.today_shares,
            stock_dividend_ratio=delta.stock_dividend_ratio,
            aum_today=delta.aum_today,
            aum_yesterday=delta.aum_yesterday,
            close_price=delta.close_price,
        )
        by_stock.setdefault(delta.stock_id, []).append(result)

    rows: list[StockConsensus] = []
    for stock_id, results in by_stock.items():
        acc_count = sum(1 for r in results if r.active_shares > 0)
        red_count = sum(1 for r in results if r.active_shares < 0)
        total_amount = sum(r.active_amount for r in results if r.active_amount > 0)

        breadth = breadth_score(acc_count, n_etfs)
        depth = depth_score(total_amount, total_aum)
        red_breadth = reduction_breadth_score(red_count, n_etfs)
        tag = classify_score(breadth, depth, breadth_thr, depth_thr)

        rows.append(
            StockConsensus(
                stock_id=stock_id,
                n_etfs=n_etfs,
                accumulate_etf_count=acc_count,
                reduction_etf_count=red_count,
                breadth_score=breadth,
                depth_score=depth,
                reduction_breadth=red_breadth,
                total_active_amount=total_amount,
                signal_tag=tag,
            )
        )

    return rows
