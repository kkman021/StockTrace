"""Integration tests for /api/etf endpoints."""


def _payload(etf_id: str = "00982A", name: str = "群益台灣ESG主動式") -> dict:
    return {
        "etf_id": etf_id,
        "etf_name": name,
        "issuer": "群益投信",
        "disclosure_url": "https://example.com/holdings",
        "aum_url": None,
        "aum_source": "inline",
        "crawler_mode": "light",
        "is_active": True,
        "notes": None,
    }


class TestEtfCrud:
    def test_list_empty_initially(self, client):
        resp = client.get("/api/etf")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_create_and_get(self, client):
        resp = client.post("/api/etf", json=_payload())
        assert resp.status_code == 201
        body = resp.json()
        assert body["etf_id"] == "00982A"
        assert body["fallback_count"] == 0
        assert body["is_active"] is True

        resp = client.get("/api/etf/00982A")
        assert resp.status_code == 200
        assert resp.json()["etf_name"] == "群益台灣ESG主動式"

    def test_create_duplicate_returns_409(self, client):
        client.post("/api/etf", json=_payload())
        resp = client.post("/api/etf", json=_payload())
        assert resp.status_code == 409

    def test_get_unknown_returns_404(self, client):
        resp = client.get("/api/etf/9999A")
        assert resp.status_code == 404

    def test_list_active_only_filters_inactive(self, client):
        client.post("/api/etf", json=_payload(etf_id="A0001"))
        client.post("/api/etf", json={**_payload(etf_id="A0002"), "is_active": False})

        resp = client.get("/api/etf?active_only=true")
        ids = [r["etf_id"] for r in resp.json()]
        assert ids == ["A0001"]

    def test_patch_updates_partial_fields(self, client):
        client.post("/api/etf", json=_payload())

        resp = client.patch(
            "/api/etf/00982A",
            json={"is_active": False, "notes": "暫時停用觀察改版"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["is_active"] is False
        assert body["notes"] == "暫時停用觀察改版"
        # 未指定的欄位保留原值
        assert body["etf_name"] == "群益台灣ESG主動式"

    def test_reset_crawler_resets_mode_and_counter(self, client, db):
        from app.models import EtfList

        client.post("/api/etf", json=_payload())
        # 模擬已自動升級到 playwright
        entry = db.get(EtfList, "00982A")
        entry.crawler_mode = "playwright"
        entry.fallback_count = 5
        db.commit()

        resp = client.post("/api/etf/00982A/reset-crawler")
        assert resp.status_code == 204

        db.expire_all()
        entry = db.get(EtfList, "00982A")
        assert entry.crawler_mode == "light"
        assert entry.fallback_count == 0

    def test_aum_override_writes_last_known_aum(self, client, db):
        from app.models import EtfList

        client.post("/api/etf", json=_payload())
        resp = client.post("/api/etf/00982A/aum", json={"aum": 1_500_000_000})
        assert resp.status_code == 204

        db.expire_all()
        assert db.get(EtfList, "00982A").last_known_aum == 1_500_000_000
