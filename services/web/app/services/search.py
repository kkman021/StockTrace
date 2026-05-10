"""OpenSearch 寫入與查詢（規格 §11.3 / §16）。

設計原則：
- Index：signal_history（每筆訊號一份文件，可全文搜尋與多維過濾）
- 寫入時機：signal_detector 成功 INSERT 一筆 signal_records 後同步寫一份到 OS
- Fail-silent：寫入或建立索引失敗皆不影響主流程；用 logger.warning 記錄
- 客戶端延遲建立：第一次呼叫才連線，避免測試或 OS 未啟動時 import 即炸
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


SIGNAL_INDEX = "signal_history"

INDEX_MAPPING = {
    "mappings": {
        "properties": {
            "date":             {"type": "date"},
            "stock_id":         {"type": "keyword"},
            "stock_name":       {"type": "text"},
            "signal_type":      {"type": "keyword"},
            "signal_tag":       {"type": "keyword"},
            "breadth_score":    {"type": "float"},
            "depth_score":      {"type": "float"},
            "consecutive_days": {"type": "integer"},
            "summary":          {"type": "text"},
        }
    }
}


@dataclass
class SignalDoc:
    date: str
    stock_id: str
    stock_name: str | None
    signal_type: str
    signal_tag: str
    breadth_score: float | None
    depth_score: float | None
    consecutive_days: int | None
    summary: str

    def doc_id(self) -> str:
        # 與 signal_records 的唯一鍵 (date, stock_id, signal_type) 對齊 → 重寫安全
        return f"{self.date}_{self.stock_id}_{self.signal_type}"

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "stock_id": self.stock_id,
            "stock_name": self.stock_name,
            "signal_type": self.signal_type,
            "signal_tag": self.signal_tag,
            "breadth_score": self.breadth_score,
            "depth_score": self.depth_score,
            "consecutive_days": self.consecutive_days,
            "summary": self.summary,
        }


class SearchClient:
    """OpenSearch 薄封裝；客戶端可注入以利測試。"""

    def __init__(self, client=None, host: str | None = None):
        self._client = client
        self._host = host or os.environ.get("OPENSEARCH_URL", "http://opensearch:9200")
        self._index_ready = False

    @property
    def client(self):
        if self._client is None:
            from opensearchpy import OpenSearch
            self._client = OpenSearch(hosts=[self._host])
        return self._client

    def ensure_index(self) -> bool:
        if self._index_ready:
            return True
        try:
            if not self.client.indices.exists(index=SIGNAL_INDEX):
                self.client.indices.create(index=SIGNAL_INDEX, body=INDEX_MAPPING)
            self._index_ready = True
            return True
        except Exception:
            logger.warning("opensearch ensure_index failed", exc_info=True)
            return False

    def index_signal(self, doc: SignalDoc) -> bool:
        if not self.ensure_index():
            return False
        try:
            self.client.index(index=SIGNAL_INDEX, id=doc.doc_id(), body=doc.to_dict())
            return True
        except Exception:
            logger.warning("opensearch index_signal failed: %s", doc.doc_id(), exc_info=True)
            return False

    def search_signals(
        self,
        q: str | None = None,
        signal_type: str | None = None,
        signal_tag: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        size: int = 50,
    ) -> dict:
        """全文 + 多維搜尋。任何欄位皆為 optional。"""
        must: list[dict] = []
        if q:
            must.append({"multi_match": {"query": q, "fields": ["stock_name", "stock_id", "summary"]}})
        if signal_type:
            must.append({"term": {"signal_type": signal_type}})
        if signal_tag:
            must.append({"term": {"signal_tag": signal_tag}})
        if date_from or date_to:
            rng: dict = {}
            if date_from:
                rng["gte"] = date_from
            if date_to:
                rng["lte"] = date_to
            must.append({"range": {"date": rng}})

        body = {
            "query": {"bool": {"must": must}} if must else {"match_all": {}},
            "size": size,
            "sort": [{"date": "desc"}],
        }
        try:
            return self.client.search(index=SIGNAL_INDEX, body=body)
        except Exception:
            logger.warning("opensearch search failed", exc_info=True)
            return {"hits": {"total": {"value": 0}, "hits": []}}


# Module-level singleton
_default: SearchClient | None = None


def get_default_client() -> SearchClient:
    global _default
    if _default is None:
        _default = SearchClient()
    return _default


def set_default_client(client: SearchClient) -> None:
    """測試或多 cluster 環境注入用。"""
    global _default
    _default = client
