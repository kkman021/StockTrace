"""減碼共識計算服務（規格 §10）。只計廣度，不計深度。"""


def reduction_breadth_score(reducing_etf_count: int, n_active_etfs: int) -> float:
    """減碼廣度 = R / N。"""
    raise NotImplementedError("TODO")


def risk_tag(breadth: float, breadth_thr: float, consec: int, consec_thr: int) -> str | None:
    """風險警示 / 觀察中 / None。"""
    raise NotImplementedError("TODO: risk-level mapping per spec §10.3")
