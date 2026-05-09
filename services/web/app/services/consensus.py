"""加碼共識計算服務（規格 §8、§9）。

三步驟主動加減碼計算，後續 Worker 與回測模組共用。
"""
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class ActivityResult:
    active_shares: int
    active_amount: int
    intensity: float
    is_new_position: bool


def compute_active_shares(
    yesterday_shares: int,
    today_shares: int,
    stock_dividend_ratio: Decimal,
    aum_today: int,
    aum_yesterday: int,
    close_price: Decimal,
) -> ActivityResult:
    """三步驟（順序不可顛倒）：
    Step1 = yesterday_shares × (1 + dividend_ratio)
    Step2 = Step1 × (aum_today / aum_yesterday)
    Step3 = today_shares - Step2
    """
    raise NotImplementedError("TODO: implement 3-step calculation per spec §4.2")


def breadth_score(accumulating_etf_count: int, n_active_etfs: int) -> float:
    """廣度分數 = M / N。"""
    raise NotImplementedError("TODO")


def depth_score(total_active_amount: int, total_aum: int) -> float:
    """深度分數 = Σ(加碼金額) / Σ(AUM)。"""
    raise NotImplementedError("TODO")


def signal_tag(breadth: float, depth: float, breadth_thr: float, depth_thr: float, consec: int, consec_thr: int) -> str | None:
    """訊號矩陣判定（規格 §9.2、§9.3、§13.3）。"""
    raise NotImplementedError("TODO: high / wide / deep / none mapping")
