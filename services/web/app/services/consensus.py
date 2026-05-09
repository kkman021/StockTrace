"""加碼共識計算服務（規格 §4、§8、§9、§13.3）。

純函數模組，無 ORM 依賴，Worker / 回測 / 單元測試共用。
"""
from dataclasses import dataclass
from decimal import Decimal


# 訊號標籤常數（與資料庫欄位 signal_tag / risk_tag 對應）
TAG_HIGH_CONSENSUS = "high_consensus"   # 高度共識
TAG_WIDE_CONSENSUS = "wide_consensus"   # 廣泛共識
TAG_DEEP_POSITION = "deep_position"     # 深度佈局


@dataclass
class ActivityResult:
    """單一 ETF 對單一持股的「主動加減碼」結果。

    - active_shares > 0 為主動加碼，< 0 為主動減碼。
    - is_new_position：今日新建倉（昨日不在持股名單）。
    - is_full_liquidation：今日全清倉（昨日有持股，今日不在持股名單）。
    """

    active_shares: int
    active_amount: int
    intensity: float
    is_new_position: bool = False
    is_full_liquidation: bool = False


def compute_active_shares(
    yesterday_shares: int,
    today_shares: int,
    stock_dividend_ratio: Decimal = Decimal("0"),
    aum_today: int | None = None,
    aum_yesterday: int | None = None,
    close_price: Decimal = Decimal("0"),
) -> ActivityResult:
    """三步驟主動加減碼計算（規格 §4.2，順序不可顛倒）：

        Step1: 配股還原後昨日股數 = 昨日股數 × (1 + 配股率)
        Step2: 規模還原後基準股數 = Step1 × (今日AUM / 昨日AUM)
        Step3: 主動加減碼股數     = 今日實際股數 − Step2

    邊界情況（規格 §8.2）：
        - 新建倉（昨日股數=0）：active_shares = today_shares，標記 is_new_position
        - 清倉（今日股數=0）：active_shares = -Step2（負值，計入減碼），標記 is_full_liquidation
        - 配股率 < 0 視為減資，與配股同邏輯（規格 §8.2）
        - AUM 缺值：跳過 Step2（視同 1.0 比例），由 caller 端決定是否納入深度分數

    Notes:
        intensity 採用 Step1 為分母，以排除 AUM 變動造成的扭曲。
        新建倉 intensity 設為 1.0（無基準可除）。
    """
    # 邊界 1：新建倉
    if yesterday_shares == 0:
        if today_shares == 0:
            return ActivityResult(0, 0, 0.0)
        amount = int(Decimal(today_shares) * close_price)
        return ActivityResult(
            active_shares=today_shares,
            active_amount=amount,
            intensity=1.0,
            is_new_position=True,
        )

    # Step1：配股還原
    step1 = Decimal(yesterday_shares) * (Decimal("1") + stock_dividend_ratio)

    # Step2：規模還原（AUM 缺值時視為 1.0）
    if aum_today is None or aum_yesterday is None or aum_yesterday == 0:
        step2 = step1
    else:
        step2 = step1 * (Decimal(aum_today) / Decimal(aum_yesterday))

    # Step3：主動加減碼
    active_shares = today_shares - int(step2)
    active_amount = int(Decimal(active_shares) * close_price)
    intensity = float(Decimal(active_shares) / step1) if step1 > 0 else 0.0

    return ActivityResult(
        active_shares=active_shares,
        active_amount=active_amount,
        intensity=intensity,
        is_full_liquidation=(today_shares == 0),
    )


def breadth_score(accumulating_etf_count: int, n_active_etfs: int) -> float:
    """廣度分數 = M / N（規格 §9.1）。"""
    if n_active_etfs <= 0:
        return 0.0
    return accumulating_etf_count / n_active_etfs


def depth_score(total_active_amount: int, total_aum: int) -> float:
    """深度分數 = Σ(加碼金額) / Σ(所有ETF的AUM)（規格 §9.1）。"""
    if total_aum <= 0:
        return 0.0
    return total_active_amount / total_aum


def classify_score(
    breadth: float,
    depth: float,
    breadth_thr: float,
    depth_thr: float,
) -> str | None:
    """每日共識分數的訊號矩陣分類（規格 §9.2，consensus_scores.signal_tag 用）。

    僅依分數高低分類，不考慮連續天數。
    """
    b_ok = breadth >= breadth_thr
    d_ok = depth >= depth_thr
    if b_ok and d_ok:
        return TAG_HIGH_CONSENSUS
    if b_ok and not d_ok:
        return TAG_WIDE_CONSENSUS
    if not b_ok and d_ok:
        return TAG_DEEP_POSITION
    return None


def trigger_signal_tag(
    breadth: float,
    depth: float,
    consec: int,
    breadth_thr: float,
    depth_thr: float,
    consec_thr: int,
) -> str | None:
    """訊號觸發判定（規格 §13.3，signal_records 用）。

    優先序：高度共識 > 廣泛共識 > 深度佈局。
        - 高度共識：廣度 ≥ 門檻 AND 深度 ≥ 門檻 AND 連續 ≥ 門檻
        - 廣泛共識：廣度 ≥ 門檻 AND 連續 ≥ 2
        - 深度佈局：深度 ≥ 門檻 AND 廣度 < 門檻
    """
    b_ok = breadth >= breadth_thr
    d_ok = depth >= depth_thr
    if b_ok and d_ok and consec >= consec_thr:
        return TAG_HIGH_CONSENSUS
    if b_ok and consec >= 2:
        return TAG_WIDE_CONSENSUS
    if d_ok and not b_ok:
        return TAG_DEEP_POSITION
    return None
