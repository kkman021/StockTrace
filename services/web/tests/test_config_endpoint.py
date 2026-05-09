"""Integration tests for /api/config endpoints."""


class TestConfigEndpoint:
    def test_get_returns_defaults_when_table_empty(self, client):
        """system_config 為空時，應回退到預設值（規格 §11.1）。"""
        resp = client.get("/api/config")
        assert resp.status_code == 200
        body = resp.json()
        assert body["breadth_threshold"] == 0.6
        assert body["depth_threshold"] == 0.6
        assert body["consecutive_days"] == 3
        assert body["sliding_window"] == 5
        assert body["reduction_breadth_threshold"] == 0.6
        assert body["reduction_consecutive_days"] == 3

    def test_patch_updates_subset_of_keys(self, client):
        resp = client.patch(
            "/api/config",
            json={"breadth_threshold": 0.7, "consecutive_days": 5},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["breadth_threshold"] == 0.7
        assert body["consecutive_days"] == 5
        # 未更新的欄位仍為預設
        assert body["depth_threshold"] == 0.6

    def test_patch_persists_across_requests(self, client):
        client.patch("/api/config", json={"sliding_window": 10})

        resp = client.get("/api/config")
        assert resp.json()["sliding_window"] == 10

    def test_patch_rejects_out_of_range(self, client):
        resp = client.patch("/api/config", json={"breadth_threshold": 0.95})
        assert resp.status_code == 422

        resp = client.patch("/api/config", json={"consecutive_days": 0})
        assert resp.status_code == 422
