"""Tests for aggregation.aggregate（規格 §8、§9）。"""
from decimal import Decimal

from app.services.aggregation import HoldingDelta, aggregate
from app.services.consensus import (
    TAG_DEEP_POSITION,
    TAG_HIGH_CONSENSUS,
    TAG_WIDE_CONSENSUS,
)


def _delta(
    etf_id: str,
    stock_id: str,
    yesterday: int,
    today: int,
    aum_t: int = 1_000_000,
    aum_y: int = 1_000_000,
    price: Decimal = Decimal("100"),
    div: Decimal = Decimal("0"),
) -> HoldingDelta:
    return HoldingDelta(
        etf_id=etf_id,
        stock_id=stock_id,
        yesterday_shares=yesterday,
        today_shares=today,
        aum_today=aum_t,
        aum_yesterday=aum_y,
        close_price=price,
        stock_dividend_ratio=div,
    )


class TestAggregate:
    def test_high_consensus_when_majority_buy_with_large_amount(self):
        """10 檔 ETF 中 8 檔加碼，加碼金額占總 AUM 70% → 高度共識。"""
        deltas = [
            _delta(f"ETF{i:02}", "2454", yesterday=0, today=10_000, price=Decimal("1000"))
            for i in range(8)
        ]
        # 2 檔不持有
        rows = aggregate(
            deltas=deltas,
            n_etfs=10,
            total_aum=100_000_000,
            breadth_thr=0.6,
            depth_thr=0.6,
        )
        assert len(rows) == 1
        row = rows[0]
        assert row.stock_id == "2454"
        assert row.accumulate_etf_count == 8
        assert row.breadth_score == 0.8
        # 8 ETFs × 10,000 shares × 1000 = 80,000,000，AUM=100M → depth=0.8
        assert row.total_active_amount == 80_000_000
        assert abs(row.depth_score - 0.8) < 1e-9
        assert row.signal_tag == TAG_HIGH_CONSENSUS

    def test_wide_consensus_breadth_high_depth_low(self):
        """多 ETF 加碼但金額小 → 廣泛共識（廣度高深度低）。"""
        deltas = [
            _delta(f"ETF{i:02}", "1234", yesterday=0, today=100, price=Decimal("10"))
            for i in range(7)
        ]
        rows = aggregate(deltas, n_etfs=10, total_aum=10_000_000_000, breadth_thr=0.6, depth_thr=0.6)
        assert rows[0].signal_tag == TAG_WIDE_CONSENSUS
        assert rows[0].breadth_score == 0.7

    def test_deep_position_low_breadth_high_depth(self):
        """少數 ETF 大量加碼 → 深度佈局（廣度低深度高）。"""
        deltas = [
            _delta(f"ETF{i:02}", "5566", yesterday=0, today=1_000_000, price=Decimal("500"))
            for i in range(2)
        ]
        # 2/10=0.2 廣度，total_amount=10億，total_aum=12億 → depth≈0.83
        rows = aggregate(deltas, n_etfs=10, total_aum=1_200_000_000, breadth_thr=0.6, depth_thr=0.6)
        assert rows[0].signal_tag == TAG_DEEP_POSITION
        assert rows[0].breadth_score == 0.2

    def test_no_signal_when_both_below_thresholds(self):
        deltas = [_delta("ETF01", "9999", yesterday=0, today=10, price=Decimal("1"))]
        rows = aggregate(deltas, n_etfs=10, total_aum=1_000_000, breadth_thr=0.6, depth_thr=0.6)
        assert rows[0].signal_tag is None

    def test_groups_multiple_stocks_independently(self):
        deltas = [
            _delta("E1", "AAA", 0, 100),
            _delta("E2", "AAA", 0, 100),
            _delta("E1", "BBB", 100, 50),  # E1 對 BBB 減碼
        ]
        rows = aggregate(deltas, n_etfs=2, total_aum=2_000_000, breadth_thr=0.6, depth_thr=0.6)
        rows_by_id = {r.stock_id: r for r in rows}
        assert rows_by_id["AAA"].accumulate_etf_count == 2
        assert rows_by_id["AAA"].reduction_etf_count == 0
        assert rows_by_id["BBB"].accumulate_etf_count == 0
        assert rows_by_id["BBB"].reduction_etf_count == 1
        assert rows_by_id["BBB"].reduction_breadth == 0.5

    def test_passive_aum_growth_does_not_count_as_active(self):
        """AUM 膨脹 30%、股數同步膨脹 30% → 主動加碼 0。"""
        deltas = [
            _delta(f"ETF{i}", "TSMC", yesterday=10_000, today=13_000, aum_t=1_300_000, aum_y=1_000_000)
            for i in range(5)
        ]
        rows = aggregate(deltas, n_etfs=5, total_aum=6_500_000, breadth_thr=0.6, depth_thr=0.6)
        assert rows[0].accumulate_etf_count == 0
        assert rows[0].reduction_etf_count == 0
        assert rows[0].breadth_score == 0.0
        assert rows[0].signal_tag is None

    def test_mixed_buy_and_sell_within_same_stock(self):
        """同一檔股票有人買有人賣，兩個 count 各自累計。"""
        deltas = [
            _delta("E1", "X", 0, 100, price=Decimal("100")),     # 加碼
            _delta("E2", "X", 0, 100, price=Decimal("100")),     # 加碼
            _delta("E3", "X", 200, 100, price=Decimal("100")),   # 減碼 -100
            _delta("E4", "X", 200, 50, price=Decimal("100")),    # 減碼 -150
        ]
        rows = aggregate(deltas, n_etfs=4, total_aum=4_000_000, breadth_thr=0.6, depth_thr=0.6)
        r = rows[0]
        assert r.accumulate_etf_count == 2
        assert r.reduction_etf_count == 2
        assert r.breadth_score == 0.5
        assert r.reduction_breadth == 0.5
        # 加碼金額 = 2 × 100 × 100 = 20,000
        assert r.total_active_amount == 20_000

    def test_aum_missing_skips_passive_adjustment(self):
        """AUM 缺值的 ETF：active_shares = today - step1（無 AUM 還原）。"""
        deltas = [
            _delta("E1", "A", 1000, 1100, aum_t=None, aum_y=None, price=Decimal("100")),
        ]
        rows = aggregate(deltas, n_etfs=1, total_aum=0, breadth_thr=0.6, depth_thr=0.6)
        assert rows[0].accumulate_etf_count == 1
        # 即便 total_aum=0，depth=0 但仍可計算廣度
        assert rows[0].depth_score == 0.0
