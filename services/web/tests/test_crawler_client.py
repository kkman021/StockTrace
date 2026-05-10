"""Tests for crawler_client (規格 §6.3, §6.4)."""
import asyncio
from datetime import date, timedelta

from app.models import EtfList, HoldingRecord
from app.services.crawler_client import (
    AUM_SOURCE_CRAWLED,
    AUM_SOURCE_MANUAL,
    AUM_SOURCE_MISSING,
    AUM_SOURCE_PREVIOUS,
    FALLBACK_UPGRADE_THRESHOLD,
    _resolve_aum,
    _update_crawler_state,
    crawl_all,
)


def _seed_etf(db, etf_id="00982A", **overrides):
    defaults = dict(
        etf_id=etf_id,
        etf_name="測試 ETF",
        issuer="測試投信",
        disclosure_url="https://example.com/holdings",
        aum_source="inline",
        crawler_mode="light",
        fallback_count=0,
        is_active=True,
    )
    defaults.update(overrides)
    e = EtfList(**defaults)
    db.add(e)
    db.commit()
    return e


def _seed_holding(db, etf_id, target_date, stock_id="2330", aum=1_000_000_000):
    db.add(
        HoldingRecord(
            etf_id=etf_id,
            date=target_date,
            stock_id=stock_id,
            shares_held=10_000,
            aum=aum,
            aum_source=AUM_SOURCE_CRAWLED,
        )
    )
    db.commit()


class TestResolveAum:
    def test_uses_crawled_when_present(self, db):
        etf = _seed_etf(db)
        target = date(2026, 5, 9)
        aum, source = _resolve_aum(db, etf, target, crawled_aum=999)
        assert aum == 999
        assert source == AUM_SOURCE_CRAWLED

    def test_falls_back_to_previous_day_aum(self, db):
        etf = _seed_etf(db)
        target = date(2026, 5, 9)
        _seed_holding(db, "00982A", target - timedelta(days=1), aum=1_500_000_000)

        aum, source = _resolve_aum(db, etf, target, crawled_aum=None)
        assert aum == 1_500_000_000
        assert source == AUM_SOURCE_PREVIOUS

    def test_skips_previous_day_with_null_aum_walks_further_back(self, db):
        etf = _seed_etf(db)
        target = date(2026, 5, 9)
        db.add(
            HoldingRecord(
                etf_id="00982A",
                date=target - timedelta(days=1),
                stock_id="X",
                shares_held=1,
                aum=None,
            )
        )
        _seed_holding(db, "00982A", target - timedelta(days=3), stock_id="Y", aum=2_000_000_000)
        db.commit()

        aum, source = _resolve_aum(db, etf, target, crawled_aum=None)
        assert aum == 2_000_000_000
        assert source == AUM_SOURCE_PREVIOUS

    def test_falls_back_to_manual_last_known_aum(self, db):
        etf = _seed_etf(db, last_known_aum=3_000_000_000)
        target = date(2026, 5, 9)
        aum, source = _resolve_aum(db, etf, target, crawled_aum=None)
        assert aum == 3_000_000_000
        assert source == AUM_SOURCE_MANUAL

    def test_marks_missing_when_no_data_available(self, db):
        etf = _seed_etf(db)
        target = date(2026, 5, 9)
        aum, source = _resolve_aum(db, etf, target, crawled_aum=None)
        assert aum is None
        assert source == AUM_SOURCE_MISSING


class TestUpdateCrawlerState:
    def test_light_success_resets_fallback_count(self):
        etf = EtfList(
            etf_id="A", etf_name="x", issuer="x", disclosure_url="x",
            crawler_mode="light", fallback_count=3,
        )
        _update_crawler_state(etf, date(2026, 5, 9), {
            "success": True, "crawler_used": "light", "light_failed": False,
        })
        assert etf.fallback_count == 0
        assert etf.crawler_mode == "light"
        assert etf.last_success_date == date(2026, 5, 9)

    def test_playwright_fallback_increments_count(self):
        etf = EtfList(
            etf_id="A", etf_name="x", issuer="x", disclosure_url="x",
            crawler_mode="light", fallback_count=2,
        )
        _update_crawler_state(etf, date(2026, 5, 9), {
            "success": True, "crawler_used": "playwright", "light_failed": True,
        })
        assert etf.fallback_count == 3
        assert etf.crawler_mode == "light"  # 還沒到門檻

    def test_threshold_auto_upgrades_to_playwright(self):
        etf = EtfList(
            etf_id="A", etf_name="x", issuer="x", disclosure_url="x",
            crawler_mode="light", fallback_count=FALLBACK_UPGRADE_THRESHOLD - 1,
        )
        _update_crawler_state(etf, date(2026, 5, 9), {
            "success": True, "crawler_used": "playwright", "light_failed": True,
        })
        assert etf.fallback_count == FALLBACK_UPGRADE_THRESHOLD
        assert etf.crawler_mode == "playwright"

    def test_failure_does_not_change_count_or_mode(self):
        etf = EtfList(
            etf_id="A", etf_name="x", issuer="x", disclosure_url="x",
            crawler_mode="light", fallback_count=1,
        )
        _update_crawler_state(etf, date(2026, 5, 9), {
            "success": False, "error": "timeout",
        })
        assert etf.fallback_count == 1
        assert etf.crawler_mode == "light"
        assert etf.last_success_date is None


class TestCrawlAll:
    """完整 crawl_single 寫入路徑使用 pg_insert（PG-only），這裡只覆蓋
    dispatcher 邏輯：誰被呼叫、retry_missing_only 過濾、active filter。
    fake fetch 一律回 success=False 以避開 _write_holdings。"""

    def test_skips_inactive_etfs(self, db):
        _seed_etf(db, etf_id="A001", is_active=True)
        _seed_etf(db, etf_id="A002", is_active=False)

        called: list[dict] = []

        async def fake_fetch(payload):
            called.append(payload)
            return {"success": False, "error": "stub", "crawler_used": "light"}

        result = asyncio.run(crawl_all(db, date(2026, 5, 9), fetch=fake_fetch))
        assert {p["etf_id"] for p in called} == {"A001"}
        assert result["attempted"] == 1
        assert result["failed"] == 1

    def test_retry_missing_only_skips_already_done(self, db):
        _seed_etf(db, etf_id="A001")
        _seed_etf(db, etf_id="A002")
        target = date(2026, 5, 9)
        _seed_holding(db, "A001", target)

        called: list[dict] = []

        async def fake_fetch(payload):
            called.append(payload)
            return {"success": False, "error": "stub"}

        result = asyncio.run(
            crawl_all(db, target, retry_missing_only=True, fetch=fake_fetch)
        )
        assert {p["etf_id"] for p in called} == {"A002"}
        assert result["attempted"] == 1
