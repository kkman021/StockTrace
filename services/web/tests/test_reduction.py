"""Tests for app.services.reduction（規格 §10）。"""
from app.services.reduction import (
    TAG_RISK_ALERT,
    TAG_WATCH,
    reduction_breadth_score,
    risk_tag,
)


class TestReductionBreadth:
    def test_basic(self):
        assert reduction_breadth_score(6, 10) == 0.6

    def test_zero_n(self):
        assert reduction_breadth_score(5, 0) == 0.0


class TestRiskTag:
    THR_B = 0.6
    THR_C = 3

    def test_risk_alert(self):
        assert risk_tag(0.7, self.THR_B, 4, self.THR_C) == TAG_RISK_ALERT

    def test_watch_when_consec_short(self):
        assert risk_tag(0.7, self.THR_B, 1, self.THR_C) == TAG_WATCH

    def test_below_breadth_threshold_returns_none(self):
        assert risk_tag(0.4, self.THR_B, 5, self.THR_C) is None

    def test_exactly_at_threshold_passes(self):
        assert risk_tag(0.6, self.THR_B, 3, self.THR_C) == TAG_RISK_ALERT
