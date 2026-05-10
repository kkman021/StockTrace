"""驗證爬取結果，決定是否觸發 fallback（規格 §6.2）。"""
from __future__ import annotations

from dataclasses import dataclass


# Reasonable lower bound — Taiwan active ETFs typically hold 30–80 stocks
MIN_HOLDINGS_RECORDS = 1
MAX_MISSING_SHARES_RATIO = 0.5

LOGIN_OR_ERROR_PATTERNS = (
    "請先登入",
    "請登入",
    "login required",
    "session expired",
    "404 not found",
    "403 forbidden",
    "service unavailable",
    "系統維護",
    "暫停服務",
    "access denied",
)


@dataclass
class ValidationResult:
    is_valid: bool
    reason: str | None = None


def validate(
    holdings: list[dict],
    raw_html: str | None = None,
    http_status: int = 200,
) -> ValidationResult:
    """驗證爬取結果（規格 §6.2）。

    任一條件不滿足即觸發 fallback：
    - HTTP 狀態碼非 200
    - holdings 為空（少於 MIN_HOLDINGS_RECORDS）
    - shares_held 缺失率 > 50%
    - HTML 內容含登入 / 錯誤頁特徵字串
    """
    if http_status != 200:
        return ValidationResult(False, f"http_status={http_status}")

    if len(holdings) < MIN_HOLDINGS_RECORDS:
        return ValidationResult(False, "no_holdings")

    missing = sum(1 for h in holdings if not h.get("shares_held"))
    if missing / len(holdings) > MAX_MISSING_SHARES_RATIO:
        return ValidationResult(
            False,
            f"shares_held_missing_ratio={missing / len(holdings):.2f}",
        )

    if raw_html:
        lower = raw_html.lower()
        for pattern in LOGIN_OR_ERROR_PATTERNS:
            if pattern in lower:
                return ValidationResult(False, f"page_pattern={pattern}")

    return ValidationResult(True)
