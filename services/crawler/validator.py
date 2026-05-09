"""驗證爬取結果，決定是否觸發 fallback（規格 §6.2）。"""


LOGIN_PAGE_PATTERNS = ["請先登入", "login", "401", "403"]


def validate_holding_records(holdings: list[dict], raw_html: str) -> tuple[bool, str | None]:
    """回傳 (is_valid, reason).

    觸發 fallback 條件（任一）：
    - holdings 為空
    - shares_held 缺失率 > 50%
    - 內容含登入頁特徵
    """
    raise NotImplementedError("TODO: implement validation rules per spec §6.2")
