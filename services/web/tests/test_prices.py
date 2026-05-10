"""Tests for derive_close_price."""
from datetime import date
from decimal import Decimal

from app.models import EtfList, HoldingRecord
from app.services.prices import derive_close_price


def _seed_etf(db, etf_id):
    db.add(EtfList(
        etf_id=etf_id, etf_name=f"Test {etf_id}", issuer="x",
        disclosure_url="x", crawler_mode="light", is_active=True,
    ))


def _seed_holding(db, etf_id, target_date, stock_id, shares, weight_pct, aum):
    db.add(HoldingRecord(
        etf_id=etf_id, date=target_date, stock_id=stock_id,
        shares_held=shares,
        weight_pct=Decimal(str(weight_pct)) if weight_pct is not None else None,
        aum=aum,
    ))


class TestDeriveClosePrice:
    def test_single_etf_holding(self, db):
        # AUM=100億, weight=20%, shares=2萬 → 100e8 * 20/100 / 20000 = 100,000
        _seed_etf(db, "A001")
        _seed_holding(db, "A001", date(2026, 5, 9), "2330", 20_000, 20.0, 10_000_000_000)
        db.commit()

        price = derive_close_price(db, "2330", date(2026, 5, 9))
        assert price is not None
        assert float(price) == 100_000.0

    def test_averages_across_multiple_etfs(self, db):
        _seed_etf(db, "A001")
        _seed_etf(db, "A002")
        # ETF1 → 100,000；ETF2: 100億 * 11/100 / 10000 = 110,000
        _seed_holding(db, "A001", date(2026, 5, 9), "2330", 20_000, 20.0, 10_000_000_000)
        _seed_holding(db, "A002", date(2026, 5, 9), "2330", 10_000, 11.0, 10_000_000_000)
        db.commit()

        price = derive_close_price(db, "2330", date(2026, 5, 9))
        assert float(price) == 105_000.0  # (100k+110k)/2

    def test_returns_none_when_no_holding(self, db):
        assert derive_close_price(db, "9999", date(2026, 5, 9)) is None

    def test_skips_rows_with_missing_components(self, db):
        _seed_etf(db, "A001")
        _seed_etf(db, "A002")
        _seed_holding(db, "A001", date(2026, 5, 9), "2330", 20_000, None, 10_000_000_000)
        _seed_holding(db, "A002", date(2026, 5, 9), "2330", 10_000, 11.0, 10_000_000_000)
        db.commit()
        # A001 缺 weight_pct → 跳過；只剩 A002 = 110,000
        price = derive_close_price(db, "2330", date(2026, 5, 9))
        assert float(price) == 110_000.0

    def test_returns_none_when_all_rows_missing_data(self, db):
        _seed_etf(db, "A001")
        _seed_holding(db, "A001", date(2026, 5, 9), "2330", 20_000, 20.0, None)
        db.commit()
        assert derive_close_price(db, "2330", date(2026, 5, 9)) is None
