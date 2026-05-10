"""Tests for validator (spec §6.2)."""
from validator import validate


def _good_holdings(n: int = 5) -> list[dict]:
    return [{"stock_id": f"S{i:04}", "shares_held": 1000 * (i + 1)} for i in range(n)]


class TestValidate:
    def test_valid_holdings(self):
        result = validate(_good_holdings(), raw_html="<html><body>ok</body></html>")
        assert result.is_valid

    def test_http_non_200_fails(self):
        result = validate(_good_holdings(), http_status=500)
        assert not result.is_valid
        assert "http_status" in result.reason

    def test_empty_holdings_fails(self):
        result = validate([])
        assert not result.is_valid
        assert result.reason == "no_holdings"

    def test_too_many_missing_shares_fails(self):
        holdings = [
            {"stock_id": "A", "shares_held": 100},
            {"stock_id": "B", "shares_held": None},
            {"stock_id": "C", "shares_held": 0},
            {"stock_id": "D", "shares_held": 0},
        ]
        # 3/4 = 0.75 missing > 0.5
        result = validate(holdings)
        assert not result.is_valid
        assert "shares_held_missing_ratio" in result.reason

    def test_login_page_pattern_fails(self):
        with open("tests/fixtures/login_required.html") as f:
            html = f.read()
        # 即便 holdings 正常,只要 HTML 有登入字樣也視為失敗
        result = validate(_good_holdings(), raw_html=html)
        assert not result.is_valid
        assert "page_pattern" in result.reason

    def test_partial_missing_within_tolerance_passes(self):
        holdings = [
            {"stock_id": "A", "shares_held": 100},
            {"stock_id": "B", "shares_held": 200},
            {"stock_id": "C", "shares_held": None},
        ]
        # 1/3 ≈ 0.33 < 0.5 → 通過
        result = validate(holdings)
        assert result.is_valid
