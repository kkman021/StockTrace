"""Integration tests for /api/consensus endpoints."""
from datetime import date, timedelta
from decimal import Decimal


def _seed_consensus(db, **overrides):
    from app.models import ConsensusScore

    defaults = dict(
        date=date(2026, 5, 9),
        stock_id="2330",
        stock_name="台積電",
        breadth_score=Decimal("0.7"),
        depth_score=Decimal("0.65"),
        accumulate_etf_count=7,
        total_amount=10_000_000,
        consecutive_days=3,
        signal_tag="high_consensus",
        reduction_breadth=Decimal("0"),
        reduction_etf_count=0,
        reduction_consec=0,
        n_etfs=10,
    )
    defaults.update(overrides)
    row = ConsensusScore(**defaults)
    db.add(row)
    db.commit()
    return row


class TestConsensusEndpoint:
    def test_latest_returns_empty_when_no_data(self, client):
        resp = client.get("/api/consensus")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_latest_returns_most_recent_date_only(self, client, db):
        _seed_consensus(db, date=date(2026, 5, 8), stock_id="2454")
        _seed_consensus(db, date=date(2026, 5, 9), stock_id="2330")
        _seed_consensus(db, date=date(2026, 5, 9), stock_id="2317")

        resp = client.get("/api/consensus")
        rows = resp.json()
        assert len(rows) == 2
        assert {r["stock_id"] for r in rows} == {"2330", "2317"}

    def test_signal_only_filter(self, client, db):
        _seed_consensus(db, stock_id="2330", signal_tag="high_consensus")
        _seed_consensus(db, stock_id="9999", signal_tag=None, breadth_score=Decimal("0.2"))

        resp = client.get("/api/consensus?signal_only=true")
        rows = resp.json()
        assert [r["stock_id"] for r in rows] == ["2330"]

    def test_consensus_by_date(self, client, db):
        _seed_consensus(db, date=date(2026, 5, 8), stock_id="2330")
        _seed_consensus(db, date=date(2026, 5, 9), stock_id="2454")

        resp = client.get("/api/consensus/2026-05-08")
        rows = resp.json()
        assert [r["stock_id"] for r in rows] == ["2330"]

    def test_consensus_by_stock_returns_history(self, client, db):
        for offset in (0, 1, 2, 3):
            _seed_consensus(
                db,
                date=date(2026, 5, 9) - timedelta(days=offset),
                stock_id="2330",
                breadth_score=Decimal("0.5") + Decimal(offset) / 10,
            )

        resp = client.get("/api/consensus/stock/2330")
        rows = resp.json()
        assert len(rows) == 4
        # 倒序排列
        assert rows[0]["date"] == "2026-05-09"

    def test_reduction_filters_to_rows_with_reduction(self, client, db):
        _seed_consensus(
            db,
            stock_id="2317",
            reduction_etf_count=6,
            reduction_breadth=Decimal("0.6"),
            reduction_consec=3,
            risk_tag="risk_alert",
        )
        # 沒有減碼的 row 不會出現
        _seed_consensus(db, stock_id="2330", reduction_etf_count=0)

        resp = client.get("/api/consensus/reduction")
        rows = resp.json()
        assert [r["stock_id"] for r in rows] == ["2317"]
