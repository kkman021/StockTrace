"""Integration tests for /api/signals list endpoint."""
from datetime import date
from decimal import Decimal


def _seed_signal(db, **overrides):
    from app.models import SignalRecord

    defaults = dict(
        date=date(2026, 5, 9),
        stock_id="2330",
        stock_name="台積電",
        signal_type="add",
        signal_tag="high_consensus",
        breadth_score=Decimal("0.7"),
        depth_score=Decimal("0.65"),
        consecutive_days=3,
    )
    defaults.update(overrides)
    row = SignalRecord(**defaults)
    db.add(row)
    db.commit()
    return row


class TestSignalsEndpoint:
    def test_list_empty(self, client):
        resp = client.get("/api/signals")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_returns_all_by_default(self, client, db):
        _seed_signal(db, stock_id="2330", signal_type="add")
        _seed_signal(db, stock_id="2317", signal_type="reduce", signal_tag="risk_alert")

        resp = client.get("/api/signals")
        rows = resp.json()
        assert len(rows) == 2

    def test_filter_by_signal_type(self, client, db):
        _seed_signal(db, stock_id="2330", signal_type="add")
        _seed_signal(db, stock_id="2317", signal_type="reduce", signal_tag="risk_alert")

        resp = client.get("/api/signals?signal_type=reduce")
        rows = resp.json()
        assert [r["stock_id"] for r in rows] == ["2317"]

    def test_filter_by_date(self, client, db):
        _seed_signal(db, date=date(2026, 5, 8), stock_id="A")
        _seed_signal(db, date=date(2026, 5, 9), stock_id="B")

        resp = client.get("/api/signals?date=2026-05-08")
        rows = resp.json()
        assert [r["stock_id"] for r in rows] == ["A"]

    def test_limit(self, client, db):
        for i in range(5):
            _seed_signal(db, stock_id=f"S{i:02}")

        resp = client.get("/api/signals?limit=3")
        assert len(resp.json()) == 3
