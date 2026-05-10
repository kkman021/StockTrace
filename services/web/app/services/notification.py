"""通知模組（規格 §13）。

抽象介面 + Web Notification 實作（Redis pub/sub）。
未來擴充 LINE / Telegram / Email。
"""
from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass

logger = logging.getLogger(__name__)


SIGNAL_CHANNEL = "signals:new"


@dataclass
class NotificationEvent:
    stock_id: str
    stock_name: str | None
    signal_type: str           # 'add' | 'reduce'
    signal_tag: str
    summary: str
    breadth_score: float | None = None
    depth_score: float | None = None
    consecutive_days: int | None = None


class NotificationChannel(ABC):
    @abstractmethod
    def send(self, event: NotificationEvent) -> bool: ...


class WebNotificationChannel(NotificationChannel):
    """Redis pub/sub publisher（規格 §13.1）。

    SSE 端點 /api/signals/stream 訂閱同一 channel 後轉送至前端，
    前端再轉成 Web Notification（規格 §23.2）。

    publish 失敗一律 fail-silent，不影響分析管線正常完成。
    """

    def __init__(self, redis_url: str | None = None):
        self._url = redis_url or os.environ.get("REDIS_URL", "redis://redis:6379/0")
        self._client = None

    @property
    def client(self):
        if self._client is None:
            import redis  # 延遲匯入，避免測試環境被迫安裝
            self._client = redis.Redis.from_url(self._url, decode_responses=True)
        return self._client

    def send(self, event: NotificationEvent) -> bool:
        try:
            payload = json.dumps(asdict(event), ensure_ascii=False)
            self.client.publish(SIGNAL_CHANNEL, payload)
            return True
        except Exception:
            logger.warning("publish to %s failed", SIGNAL_CHANNEL, exc_info=True)
            return False


# Module-level singleton；signal_detector 直接呼叫
_default: NotificationChannel | None = None


def get_default_channel() -> NotificationChannel:
    global _default
    if _default is None:
        _default = WebNotificationChannel()
    return _default


def set_default_channel(channel: NotificationChannel) -> None:
    """測試或多通道整合時可注入替代實作。"""
    global _default
    _default = channel


# 未來擴充：
# class LineNotificationChannel(NotificationChannel): ...
# class TelegramNotificationChannel(NotificationChannel): ...
# class EmailNotificationChannel(NotificationChannel): ...
