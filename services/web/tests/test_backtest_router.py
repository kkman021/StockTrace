"""Router-level tests for /api/backtest."""
from datetime import date, timedelta
from decimal import Decimal

from app.models import ConsensusScore, EtfList, HoldingRecord


def _seed_environment(db):
    db.add(EtfList(
        etf_id="A001", etf_name="x", issuer="x",
        disclosure_url="x", crawler_mode="light", is_active=True,
    ))
    base = date(2026, 5, 1)
    days = [base + timedelta(days=i) for i in range(11)]
    pattern = [(0.7, 0.7)] * 4 + [(0.3, 0.3)] + [(0.7, 0.7)] * 6
    for d, (b, dp) in zip(days, pattern):
        db.add(ConsensusScore(
            date=d, stock_id="2330", stock_name="台積電",
            breadth_score=Decimal(str(b)), depth_score=Decimal(str(dp)),
        ))
    for i, d in enumerate(days):
        db.add(HoldingRecord(
            etf_id="A001", date=d, stock_id="2330",
            shares_held=10_000, weight_pct=Decimal("10.0"),
            aum=int((100 + 10 * i) * 100_000),
        ))
    db.commit()
    return days


class TestCreateBacktest:
    def test_creates_run_and_executes_synchronously(self, client, db):
        days = _seed_environment(db)
        resp = client.post("/api/backtest", json={
            "start_date": days[0].isoformat(),
            "end_date": days[-1].isoformat(),
            "holding_days": 2,
            "breadth_threshold": 0.6,
            "depth_threshold": 0.6,
            "consecutive_days": 3,
        })
        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "completed"

    def test_validates_date_range(self, client, db):
        _seed_environment(db)
        resp = client.post("/api/backtest", json={
            "start_date": "2026-05-10",
            "end_date": "2026-05-01",
            "holding_days": 2,
            "breadth_threshold": 0.6,
            "depth_threshold": 0.6,
            "consecutive_days": 3,
        })
        assert resp.status_code == 400


class TestGetSummaryAndChart:
    def test_summary_and_chart_after_run(self, client, db):
        days = _seed_environment(db)
        create = client.post("/api/backtest", json={
            "start_date": days[0].isoformat(),
            "end_date": days[-1].isoformat(),
            "holding_days": 2,
            "breadth_threshold": 0.6,
            "depth_threshold": 0.6,
            "consecutive_days": 3,
        })
        run_id = create.json()["id"]

        summary = client.get(f"/api/backtest/{run_id}/summary").json()
        assert len(summary) == 1
        assert summary[0]["stock_id"] == "2330"
        assert summary[0]["trigger_count"] == 2

        chart = client.get(f"/api/backtest/{run_id}/chart/2330").json()
        assert chart["trigger_count"] == 2
        assert len(chart["avg_line"]) > 0

    def test_404_for_unknown_run(self, client):
        assert client.get("/api/backtest/9999").status_code == 404
        assert client.get("/api/backtest/9999/summary").status_code == 404
        assert client.get("/api/backtest/9999/chart/2330").status_code == 404
