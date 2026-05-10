"""Tests for backtest engine (規格 §12)。"""
from datetime import date, timedelta
from decimal import Decimal

from app.models import BacktestResult, BacktestRun, ConsensusScore, EtfList, HoldingRecord
from app.services import backtest as bt


# ---------- helpers ---------- #

def _seed_etf(db, etf_id="A001"):
    db.add(EtfList(
        etf_id=etf_id, etf_name=f"Test {etf_id}", issuer="x",
        disclosure_url="x", crawler_mode="light", is_active=True,
    ))


def _seed_consensus(db, target_date, stock_id, breadth, depth, name=None):
    db.add(ConsensusScore(
        date=target_date,
        stock_id=stock_id,
        stock_name=name,
        breadth_score=Decimal(str(breadth)),
        depth_score=Decimal(str(depth)),
    ))


def _seed_price(db, target_date, stock_id, price, etf_id="A001"):
    """讓 derived_close_price 剛好等於 price。
    formula: AUM × weight/100 / shares
    取 shares=10_000, weight=10 → AUM = price × 100_000 即可使 derived = price。
    """
    db.add(HoldingRecord(
        etf_id=etf_id, date=target_date, stock_id=stock_id,
        shares_held=10_000,
        weight_pct=Decimal("10.0"),
        aum=int(price * 100_000),
    ))


def _setup_full_dataset(db):
    """11 個交易日，2330 前 4 天連續達標、第 5 天斷、第 6 天起又連 6 天達標。

    保留兩條 streak 都有足夠未來日，讓 buy/sell 與 series 都能完整產出。
    """
    _seed_etf(db, "A001")
    base = date(2026, 5, 1)
    days = [base + timedelta(days=i) for i in range(11)]
    pattern_2330 = (
        [(0.7, 0.7)] * 4 + [(0.3, 0.3)] + [(0.7, 0.7)] * 6
    )
    pattern_2454 = [(0.5, 0.5)] * 11
    for d, (b, dp) in zip(days, pattern_2330):
        _seed_consensus(db, d, "2330", b, dp, name="台積電")
    for d, (b, dp) in zip(days, pattern_2454):
        _seed_consensus(db, d, "2454", b, dp)

    # 遞增價格 100, 110, 120, ...
    for i, d in enumerate(days):
        _seed_price(db, d, "2330", 100 + 10 * i)
    db.commit()
    return days


# ---------- scan_triggers ---------- #

class TestScanTriggers:
    def test_rising_edge_only_fires_once_per_streak(self, db):
        days = _setup_full_dataset(db)
        triggers = bt.scan_triggers(
            db, start=days[0], end=days[-1],
            breadth_thr=0.6, depth_thr=0.6, consec=3,
        )
        # 應有兩次觸發：第 3 天（第一條 streak 達 3）+ 第 8 天（第二條 streak 達 3）
        # idx=2 (date 2026-05-03) 與 idx=7 (date 2026-05-08)
        assert [t.trigger_date for t in triggers] == [days[2], days[7]]
        assert all(t.stock_id == "2330" for t in triggers)

    def test_skips_stocks_below_threshold(self, db):
        days = _setup_full_dataset(db)
        triggers = bt.scan_triggers(
            db, start=days[0], end=days[-1],
            breadth_thr=0.6, depth_thr=0.6, consec=3,
        )
        assert all(t.stock_id != "2454" for t in triggers)

    def test_target_stocks_filter(self, db):
        days = _setup_full_dataset(db)
        triggers = bt.scan_triggers(
            db, start=days[0], end=days[-1],
            breadth_thr=0.6, depth_thr=0.6, consec=3,
            target_stocks=["9999"],  # 不存在
        )
        assert triggers == []

    def test_window_excludes_triggers_outside_range(self, db):
        days = _setup_full_dataset(db)
        # 只看後 3 天 → 只剩第 8 天那次觸發
        triggers = bt.scan_triggers(
            db, start=days[5], end=days[-1],
            breadth_thr=0.6, depth_thr=0.6, consec=3,
        )
        assert len(triggers) == 1
        assert triggers[0].trigger_date == days[7]

    def test_higher_consec_requirement_filters_out(self, db):
        days = _setup_full_dataset(db)
        # 兩條 streak 長度分別為 4 與 6 → consec=7 都不到
        triggers = bt.scan_triggers(
            db, start=days[0], end=days[-1],
            breadth_thr=0.6, depth_thr=0.6, consec=7,
        )
        assert triggers == []


# ---------- run_backtest end-to-end ---------- #

class TestRunBacktest:
    def test_writes_results_and_marks_completed(self, db):
        days = _setup_full_dataset(db)
        run = BacktestRun(
            start_date=days[0], end_date=days[-1],
            holding_days=2, breadth_threshold=Decimal("0.6"),
            depth_threshold=Decimal("0.6"), consecutive_days=3,
            status="pending",
        )
        db.add(run); db.commit(); db.refresh(run)

        stats = bt.run_backtest(db, run)
        assert stats["triggers"] == 2
        assert run.status == "completed"
        assert run.completed_at is not None

        results = db.query(BacktestResult).filter_by(run_id=run.id).all()
        assert len(results) == 2

    def test_return_calculation(self, db):
        days = _setup_full_dataset(db)
        # 第一次觸發：trigger=day[2]，buy=day[3] (價 130)，holding=2 → sell=day[5] (價 150)
        # return = (150-130)/130 = 0.1538...
        run = BacktestRun(
            start_date=days[0], end_date=days[-1],
            holding_days=2, breadth_threshold=Decimal("0.6"),
            depth_threshold=Decimal("0.6"), consecutive_days=3,
            status="pending",
        )
        db.add(run); db.commit(); db.refresh(run)
        bt.run_backtest(db, run)

        first = db.query(BacktestResult).filter_by(
            run_id=run.id, trigger_date=days[2]
        ).first()
        assert first.is_valid
        assert first.buy_date == days[3]
        assert first.sell_date == days[5]
        assert float(first.buy_price) == 130.0
        assert float(first.sell_price) == 150.0
        assert abs(float(first.return_rate) - (20 / 130)) < 0.0001

    def test_invalid_when_insufficient_future_days(self, db):
        days = _setup_full_dataset(db)
        # holding_days=10 → 任何觸發都缺未來資料
        run = BacktestRun(
            start_date=days[0], end_date=days[-1],
            holding_days=10, breadth_threshold=Decimal("0.6"),
            depth_threshold=Decimal("0.6"), consecutive_days=3,
            status="pending",
        )
        db.add(run); db.commit(); db.refresh(run)
        bt.run_backtest(db, run)

        results = db.query(BacktestResult).filter_by(run_id=run.id).all()
        assert all(not r.is_valid for r in results)
        assert all(r.invalid_reason == "insufficient_future_days" for r in results)

    def test_target_stocks_passed_through(self, db):
        days = _setup_full_dataset(db)
        run = BacktestRun(
            start_date=days[0], end_date=days[-1],
            holding_days=2, breadth_threshold=Decimal("0.6"),
            depth_threshold=Decimal("0.6"), consecutive_days=3,
            target_stocks=["9999"],
            status="pending",
        )
        db.add(run); db.commit(); db.refresh(run)
        stats = bt.run_backtest(db, run)
        assert stats["triggers"] == 0


# ---------- aggregate_summary ---------- #

class TestAggregateSummary:
    def test_summary_aggregates_per_stock(self, db):
        days = _setup_full_dataset(db)
        run = BacktestRun(
            start_date=days[0], end_date=days[-1],
            holding_days=2, breadth_threshold=Decimal("0.6"),
            depth_threshold=Decimal("0.6"), consecutive_days=3,
            status="pending",
        )
        db.add(run); db.commit(); db.refresh(run)
        bt.run_backtest(db, run)

        summary = bt.aggregate_summary(db, run.id)
        assert len(summary) == 1
        row = summary[0]
        assert row["stock_id"] == "2330"
        assert row["trigger_count"] == 2
        # 兩次觸發都正報酬 → win_rate = 1.0
        assert row["win_rate"] == 1.0
        assert row["max_return"] >= row["min_return"]
        assert row["avg_return"] > 0


# ---------- chart payload ---------- #

class TestBuildChartPayload:
    def test_chart_has_normalized_lines_and_avg(self, db):
        days = _setup_full_dataset(db)
        run = BacktestRun(
            start_date=days[0], end_date=days[-1],
            holding_days=2, breadth_threshold=Decimal("0.6"),
            depth_threshold=Decimal("0.6"), consecutive_days=3,
            status="pending",
        )
        db.add(run); db.commit(); db.refresh(run)
        bt.run_backtest(db, run)

        payload = bt.build_chart_payload(db, run.id, "2330")
        assert payload["stock_id"] == "2330"
        assert payload["trigger_count"] == 2
        assert len(payload["series"]) == 2
        # 每條 line 的第一個點 ratio 應為 1.0（normalized to buy price）
        for s in payload["series"]:
            assert s["line"][0]["ratio"] == 1.0
        # avg_line 對齊 offset
        assert payload["avg_line"][0]["ratio"] == 1.0
