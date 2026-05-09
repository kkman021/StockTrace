"""減碼共識計算服務（規格 §10）。

只計廣度，不計深度（用於風險警示，不作放空依據）。
"""

TAG_RISK_ALERT = "risk_alert"   # 風險警示
TAG_WATCH = "watch"             # 觀察中


def reduction_breadth_score(reducing_etf_count: int, n_active_etfs: int) -> float:
    """減碼廣度分數 = R / N（規格 §10.2）。"""
    if n_active_etfs <= 0:
        return 0.0
    return reducing_etf_count / n_active_etfs


def risk_tag(
    reduction_breadth: float,
    breadth_thr: float,
    consec: int,
    consec_thr: int,
) -> str | None:
    """減碼風險警示判定（規格 §10.3）。

        - 風險警示：廣度 ≥ 門檻 AND 連續 ≥ 門檻
        - 觀察中：廣度 ≥ 門檻 AND 連續 < 門檻
    """
    if reduction_breadth < breadth_thr:
        return None
    return TAG_RISK_ALERT if consec >= consec_thr else TAG_WATCH
