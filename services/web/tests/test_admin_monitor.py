"""Tests for admin /crawl-status + /search-signals."""
from datetime import date
from unittest.mock import MagicMock

from app.models import CrawlLog, EtfList
from app.services import search as search_module


def _seed_etfs(db):
    db.add(EtfList(
        etf_id="A001", etf_name="ETF A", issuer="x",
        disclosure_url="x", crawler_mode="light",
        fallback_count=0, is_active=True, last_success_date=date(2026, 5, 8),
    ))
    db.add(EtfList(
        etf_id="A002", etf_name="ETF B", issuer="x",
        disclosure_url="x", crawler_mode="playwright",
        fallback_count=5, is_active=True,
    ))
    db.add(EtfList(
        etf_id="X999", etf_name="Inactive", issuer="x",
        disclosure_url="x", crawler_mode="light", is_active=False,
    ))
    db.commit()


class TestCrawlStatus:
    def test_lists_active_etfs_only(self, client, db):
        _seed_etfs(db)
        resp = client.get("/api/admin/crawl-status?date=2026-05-09").json()
        ids = [x["etf_id"] for x in resp["items"]]
        assert ids == ["A001", "A002"]
        assert resp["total"] == 2

    def test_today_log_attached_when_present(self, client, db):
        _seed_etfs(db)
        target = date(2026, 5, 9)
        db.add(CrawlLog(
            etf_id="A001", crawl_date=target, crawler_used="light",
            status="success", records_count=42, duration_ms=1234,
        ))
        # 兩筆同一天，應只取最新（id 大的）
        db.add(CrawlLog(
            etf_id="A001", crawl_date=target, crawler_used="playwright",
            status="failed", records_count=0, duration_ms=5000,
            error_message="timeout",
        ))
        db.commit()

        resp = client.get(f"/api/admin/crawl-status?date={target.isoformat()}").json()
        a001 = next(x for x in resp["items"] if x["etf_id"] == "A001")
        a002 = next(x for x in resp["items"] if x["etf_id"] == "A002")

        # A001 的最新 log 是失敗那筆
        assert a001["today_log"]["status"] == "failed"
        assert a001["today_log"]["error_message"] == "timeout"
        # A002 沒有 log
        assert a002["today_log"] is None
        # success_today 計入有 log 且 status=success 的（A001 最新是 failed → 0）
        assert resp["success_today"] == 0

    def test_success_today_counted_correctly(self, client, db):
        _seed_etfs(db)
        target = date(2026, 5, 9)
        db.add(CrawlLog(
            etf_id="A001", crawl_date=target, status="success",
            crawler_used="light", records_count=30, duration_ms=900,
        ))
        db.commit()
        resp = client.get(f"/api/admin/crawl-status?date={target.isoformat()}").json()
        assert resp["success_today"] == 1


class TestSearchSignals:
    def test_passes_filters_to_client(self, client, db):
        fake = MagicMock()
        fake.search_signals.return_value = {
            "hits": {"total": {"value": 1}, "hits": [
                {"_source": {"stock_id": "2330", "stock_name": "台積電"}}
            ]}
        }
        search_module.set_default_client(fake)
        try:
            resp = client.get(
                "/api/admin/search-signals",
                params={"q": "台積", "signal_type": "add", "size": 20},
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body["total"] == 1
            assert body["items"][0]["stock_id"] == "2330"

            kwargs = fake.search_signals.call_args.kwargs
            assert kwargs["q"] == "台積"
            assert kwargs["signal_type"] == "add"
            assert kwargs["size"] == 20
        finally:
            search_module.set_default_client(None)
            search_module._default = None

    def test_returns_empty_when_no_results(self, client, db):
        fake = MagicMock()
        fake.search_signals.return_value = {"hits": {"total": {"value": 0}, "hits": []}}
        search_module.set_default_client(fake)
        try:
            resp = client.get("/api/admin/search-signals").json()
            assert resp["total"] == 0
            assert resp["items"] == []
        finally:
            search_module.set_default_client(None)
            search_module._default = None
