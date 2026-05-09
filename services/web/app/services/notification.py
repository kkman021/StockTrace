"""通知模組（規格 §13）。

抽象介面 + Web Notification 實作。未來擴充 LINE / Telegram / Email。
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class NotificationEvent:
    stock_id: str
    stock_name: str | None
    signal_tag: str
    summary: str
    breadth_score: float | None
    depth_score: float | None
    consecutive_days: int | None


class NotificationChannel(ABC):
    @abstractmethod
    def send(self, event: NotificationEvent) -> bool: ...


class WebNotificationChannel(NotificationChannel):
    """v1.0：透過 Redis pub/sub 廣播給 SSE 連線。"""

    def send(self, event: NotificationEvent) -> bool:
        raise NotImplementedError("TODO: publish to Redis channel `signals:new`")


# 未來擴充：
# class LineNotificationChannel(NotificationChannel): ...
# class TelegramNotificationChannel(NotificationChannel): ...
# class EmailNotificationChannel(NotificationChannel): ...
