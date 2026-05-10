"""Tests for OpenSearch wrapper (規格 §11.3)。"""
from unittest.mock import MagicMock

from app.services.search import (
    INDEX_MAPPING,
    SIGNAL_INDEX,
    SearchClient,
    SignalDoc,
)


def _doc(**overrides):
    base = dict(
        date="2026-05-09", stock_id="2330", stock_name="台積電",
        signal_type="add", signal_tag="high_consensus",
        breadth_score=0.75, depth_score=0.65, consecutive_days=3,
        summary="高度共識：台積電（2330）",
    )
    base.update(overrides)
    return SignalDoc(**base)


class TestSignalDoc:
    def test_doc_id_combines_three_keys(self):
        assert _doc().doc_id() == "2026-05-09_2330_add"

    def test_to_dict_round_trip(self):
        d = _doc().to_dict()
        assert d["stock_id"] == "2330"
        assert d["depth_score"] == 0.65
        assert "summary" in d


class TestSearchClient:
    def test_ensure_index_creates_when_missing(self):
        client = MagicMock()
        client.indices.exists.return_value = False
        sc = SearchClient(client=client)
        assert sc.ensure_index() is True
        client.indices.create.assert_called_once_with(index=SIGNAL_INDEX, body=INDEX_MAPPING)

    def test_ensure_index_skips_when_exists(self):
        client = MagicMock()
        client.indices.exists.return_value = True
        sc = SearchClient(client=client)
        assert sc.ensure_index() is True
        client.indices.create.assert_not_called()

    def test_ensure_index_caches_result(self):
        client = MagicMock()
        client.indices.exists.return_value = True
        sc = SearchClient(client=client)
        sc.ensure_index()
        sc.ensure_index()
        sc.ensure_index()
        # exists 只查 1 次（idempotent cache）
        assert client.indices.exists.call_count == 1

    def test_ensure_index_swallows_errors(self):
        client = MagicMock()
        client.indices.exists.side_effect = ConnectionError("opensearch down")
        assert SearchClient(client=client).ensure_index() is False

    def test_index_signal_writes_with_doc_id(self):
        client = MagicMock()
        client.indices.exists.return_value = True
        sc = SearchClient(client=client)
        doc = _doc()
        assert sc.index_signal(doc) is True
        client.index.assert_called_once()
        call = client.index.call_args
        assert call.kwargs["index"] == SIGNAL_INDEX
        assert call.kwargs["id"] == doc.doc_id()
        assert call.kwargs["body"]["stock_id"] == "2330"

    def test_index_signal_skips_on_index_error(self):
        client = MagicMock()
        client.indices.exists.return_value = True
        client.index.side_effect = RuntimeError("conflict")
        assert SearchClient(client=client).index_signal(_doc()) is False

    def test_search_with_filters(self):
        client = MagicMock()
        client.search.return_value = {"hits": {"total": {"value": 2}, "hits": []}}
        sc = SearchClient(client=client)

        sc.search_signals(
            q="台積", signal_type="add", signal_tag="high_consensus",
            date_from="2026-05-01", date_to="2026-05-09",
        )

        body = client.search.call_args.kwargs["body"]
        must = body["query"]["bool"]["must"]
        # 4 個過濾條件：q / signal_type / signal_tag / date range
        assert len(must) == 4
        assert any("multi_match" in m for m in must)
        assert any(m.get("term", {}).get("signal_type") == "add" for m in must)
        assert any("range" in m for m in must)
        assert body["sort"] == [{"date": "desc"}]

    def test_search_match_all_when_no_filter(self):
        client = MagicMock()
        client.search.return_value = {"hits": {"total": {"value": 0}, "hits": []}}
        SearchClient(client=client).search_signals()

        body = client.search.call_args.kwargs["body"]
        assert body["query"] == {"match_all": {}}

    def test_search_returns_empty_on_error(self):
        client = MagicMock()
        client.search.side_effect = RuntimeError("os down")
        result = SearchClient(client=client).search_signals(q="x")
        assert result == {"hits": {"total": {"value": 0}, "hits": []}}
