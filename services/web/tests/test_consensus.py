"""Tests for app.services.consensus.

對應規格 §4.2、§9、§13.3。
"""
from decimal import Decimal

import pytest

from app.services.consensus import (
    TAG_DEEP_POSITION,
    TAG_HIGH_CONSENSUS,
    TAG_WIDE_CONSENSUS,
    breadth_score,
    classify_score,
    compute_active_shares,
    depth_score,
    trigger_signal_tag,
)


class TestComputeActiveShares:
    def test_spec_canonical_example(self):
        """規格 §4.2 範例：昨 100k × 1.1 × 1.05 = 115,500，今 116,000，主動 +500。"""
        result = compute_active_shares(
            yesterday_shares=100_000,
            today_shares=116_000,
            stock_dividend_ratio=Decimal("0.1"),
            aum_today=1_050_000_000,
            aum_yesterday=1_000_000_000,
            close_price=Decimal("100"),
        )
        assert result.active_shares == 500
        assert result.active_amount == 50_000
        assert not result.is_new_position
        assert not result.is_full_liquidation

    def test_no_dividend_no_aum_change(self):
        """無配股、AUM 不變：主動加減碼 = 今日 - 昨日。"""
        result = compute_active_shares(
            yesterday_shares=10_000,
            today_shares=12_000,
            aum_today=1_000_000,
            aum_yesterday=1_000_000,
            close_price=Decimal("50"),
        )
        assert result.active_shares == 2_000
        assert result.active_amount == 100_000

    def test_aum_growth_creates_passive_increase_filtered_out(self):
        """ETF 規模膨脹 20%，今日股數同步膨脹 20%：主動加減碼應 ≈ 0。"""
        result = compute_active_shares(
            yesterday_shares=10_000,
            today_shares=12_000,
            aum_today=1_200_000,
            aum_yesterday=1_000_000,
            close_price=Decimal("100"),
        )
        assert result.active_shares == 0

    def test_new_position_marked(self):
        """昨日無持股、今日有持股：視為 100% 主動買入。"""
        result = compute_active_shares(
            yesterday_shares=0,
            today_shares=5_000,
            close_price=Decimal("80"),
        )
        assert result.is_new_position is True
        assert result.active_shares == 5_000
        assert result.active_amount == 400_000
        assert result.intensity == 1.0

    def test_both_zero_returns_zero(self):
        result = compute_active_shares(yesterday_shares=0, today_shares=0)
        assert result.active_shares == 0
        assert not result.is_new_position

    def test_full_liquidation(self):
        """昨日有持股、今日清倉：active_shares 為負，標記 is_full_liquidation。"""
        result = compute_active_shares(
            yesterday_shares=10_000,
            today_shares=0,
            aum_today=1_000_000,
            aum_yesterday=1_000_000,
            close_price=Decimal("50"),
        )
        assert result.is_full_liquidation is True
        assert result.active_shares == -10_000
        assert result.active_amount == -500_000

    def test_aum_missing_skips_scale_adjustment(self):
        """AUM 缺值：跳過規模還原，僅做配股還原。"""
        result = compute_active_shares(
            yesterday_shares=10_000,
            today_shares=11_000,
            stock_dividend_ratio=Decimal("0"),
            aum_today=None,
            aum_yesterday=None,
            close_price=Decimal("100"),
        )
        # step1=10000, step2=10000 (AUM skipped), active=1000
        assert result.active_shares == 1_000

    def test_capital_reduction_negative_dividend_ratio(self):
        """減資（規格 §8.2）：配股率為負，與配股同邏輯。

        昨 10,000 × (1 - 0.2) = 8,000；AUM 不變；今 9,000 → 主動 +1,000。
        """
        result = compute_active_shares(
            yesterday_shares=10_000,
            today_shares=9_000,
            stock_dividend_ratio=Decimal("-0.2"),
            aum_today=1_000_000,
            aum_yesterday=1_000_000,
            close_price=Decimal("100"),
        )
        assert result.active_shares == 1_000

    def test_negative_active_shares_indicates_reduction(self):
        """今日股數低於基準：主動減碼。"""
        result = compute_active_shares(
            yesterday_shares=10_000,
            today_shares=8_000,
            aum_today=1_000_000,
            aum_yesterday=1_000_000,
            close_price=Decimal("60"),
        )
        assert result.active_shares == -2_000
        assert result.active_amount == -120_000


class TestBreadthScore:
    def test_basic(self):
        assert breadth_score(7, 10) == 0.7

    def test_zero_n_returns_zero(self):
        assert breadth_score(5, 0) == 0.0


class TestDepthScore:
    def test_basic(self):
        assert depth_score(50, 1000) == 0.05

    def test_zero_aum_returns_zero(self):
        assert depth_score(100, 0) == 0.0


class TestClassifyScore:
    THR_B = 0.6
    THR_D = 0.6

    def test_high_consensus(self):
        assert classify_score(0.7, 0.8, self.THR_B, self.THR_D) == TAG_HIGH_CONSENSUS

    def test_wide_consensus(self):
        assert classify_score(0.7, 0.4, self.THR_B, self.THR_D) == TAG_WIDE_CONSENSUS

    def test_deep_position(self):
        assert classify_score(0.4, 0.7, self.THR_B, self.THR_D) == TAG_DEEP_POSITION

    def test_no_signal(self):
        assert classify_score(0.4, 0.4, self.THR_B, self.THR_D) is None

    def test_exactly_at_threshold_counts_as_pass(self):
        assert classify_score(0.6, 0.6, self.THR_B, self.THR_D) == TAG_HIGH_CONSENSUS


class TestTriggerSignalTag:
    THR_B = 0.6
    THR_D = 0.6
    THR_C = 3

    def test_high_consensus_requires_consec(self):
        assert (
            trigger_signal_tag(0.7, 0.7, 3, self.THR_B, self.THR_D, self.THR_C)
            == TAG_HIGH_CONSENSUS
        )

    def test_high_score_but_short_consec_falls_to_wide(self):
        """廣度+深度都過、連續=2：未達高度共識，但符合廣泛共識（≥2 日）。"""
        assert (
            trigger_signal_tag(0.7, 0.7, 2, self.THR_B, self.THR_D, self.THR_C)
            == TAG_WIDE_CONSENSUS
        )

    def test_wide_consensus_breadth_only(self):
        assert (
            trigger_signal_tag(0.7, 0.4, 2, self.THR_B, self.THR_D, self.THR_C)
            == TAG_WIDE_CONSENSUS
        )

    def test_wide_requires_consec_at_least_2(self):
        assert (
            trigger_signal_tag(0.7, 0.4, 1, self.THR_B, self.THR_D, self.THR_C)
            is None
        )

    def test_deep_position_no_consec_requirement(self):
        assert (
            trigger_signal_tag(0.4, 0.7, 1, self.THR_B, self.THR_D, self.THR_C)
            == TAG_DEEP_POSITION
        )

    def test_no_signal(self):
        assert (
            trigger_signal_tag(0.3, 0.3, 5, self.THR_B, self.THR_D, self.THR_C)
            is None
        )
