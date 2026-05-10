"""通知模組（規格 §13）。

多通道實作：
- WebNotificationChannel: Redis pub/sub → SSE → 前端 Web Notification（規格 §13.1 / §23.2）
- SlackChannel: Incoming Webhook
- LineChannel: LINE Notify (Bearer token)
- EmailChannel: SMTP，多收件人逗號分隔
- CompositeChannel: 一次扇出多通道，個別失敗不影響其他

預設通道由 NOTIFICATION_CHANNELS 環境變數決定（逗號分隔，例 "web,slack,line"），
未設定時回退單一 web 通道，保留舊行為相容。所有通道皆 fail-silent，不影響分析管線。
"""
from __future__ import annotations

import json
import logging
import os
import smtplib
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from email.message import EmailMessage

import httpx

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


def _format_message(event: NotificationEvent) -> str:
    """共用文字格式化（Slack / LINE / Email 都用這個）。"""
    emoji = "🚨" if event.signal_type == "reduce" else "📈"
    parts: list[str] = []
    if event.breadth_score is not None:
        parts.append(f"廣度 {event.breadth_score:.2f}")
    if event.depth_score is not None:
        parts.append(f"深度 {event.depth_score:.2f}")
    if event.consecutive_days is not None:
        parts.append(f"連續 {event.consecutive_days} 日")
    suffix = f"（{' / '.join(parts)}）" if parts else ""
    return f"{emoji} {event.summary}{suffix}"


# ---------- Web (Redis pub/sub) ---------- #

class WebNotificationChannel(NotificationChannel):
    """SSE 端點 /api/signals/stream 訂閱同一 channel 後轉送至前端。"""

    def __init__(self, redis_url: str | None = None):
        self._url = redis_url or os.environ.get("REDIS_URL", "redis://redis:6379/0")
        self._client = None

    @property
    def client(self):
        if self._client is None:
            import redis  # 延遲匯入
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


# ---------- Slack ---------- #

class SlackChannel(NotificationChannel):
    """Slack Incoming Webhook。"""

    def __init__(self, webhook_url: str | None = None, http_client: httpx.Client | None = None):
        self.webhook_url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL", "")
        self._http = http_client

    def send(self, event: NotificationEvent) -> bool:
        if not self.webhook_url:
            logger.debug("SlackChannel disabled (no webhook url)")
            return False
        try:
            client = self._http or httpx.Client(timeout=10.0)
            try:
                resp = client.post(self.webhook_url, json={"text": _format_message(event)})
            finally:
                if self._http is None:
                    client.close()
            return 200 <= resp.status_code < 300
        except Exception:
            logger.warning("slack send failed", exc_info=True)
            return False


# ---------- LINE Notify ---------- #

class LineChannel(NotificationChannel):
    """LINE Notify (Bearer token)。"""

    NOTIFY_URL = "https://notify-api.line.me/api/notify"

    def __init__(self, token: str | None = None, http_client: httpx.Client | None = None):
        self.token = token or os.environ.get("LINE_NOTIFY_TOKEN", "")
        self._http = http_client

    def send(self, event: NotificationEvent) -> bool:
        if not self.token:
            logger.debug("LineChannel disabled (no token)")
            return False
        try:
            client = self._http or httpx.Client(timeout=10.0)
            try:
                resp = client.post(
                    self.NOTIFY_URL,
                    headers={"Authorization": f"Bearer {self.token}"},
                    data={"message": "\n" + _format_message(event)},
                )
            finally:
                if self._http is None:
                    client.close()
            return resp.status_code == 200
        except Exception:
            logger.warning("line notify failed", exc_info=True)
            return False


# ---------- Email (SMTP) ---------- #

class EmailChannel(NotificationChannel):
    """SMTP 寄信。

    config 走 env：
    - SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASSWORD
    - EMAIL_FROM / EMAIL_TO（逗號分隔）
    - SMTP_USE_TLS=1 開啟 starttls
    """

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        user: str | None = None,
        password: str | None = None,
        sender: str | None = None,
        recipients: str | None = None,
        use_tls: bool | None = None,
        smtp_factory=None,  # 測試注入
    ):
        self.host = host if host is not None else os.environ.get("SMTP_HOST", "")
        self.port = port if port is not None else int(os.environ.get("SMTP_PORT", "587"))
        self.user = user if user is not None else os.environ.get("SMTP_USER", "")
        self.password = password if password is not None else os.environ.get("SMTP_PASSWORD", "")
        self.sender = sender if sender is not None else os.environ.get("EMAIL_FROM", self.user)
        recipients = recipients if recipients is not None else os.environ.get("EMAIL_TO", "")
        self.recipients = [x.strip() for x in recipients.split(",") if x.strip()]
        self.use_tls = use_tls if use_tls is not None else os.environ.get("SMTP_USE_TLS", "1") == "1"
        self._smtp_factory = smtp_factory or smtplib.SMTP

    def send(self, event: NotificationEvent) -> bool:
        if not (self.host and self.recipients and self.sender):
            logger.debug("EmailChannel disabled (incomplete config)")
            return False
        msg = EmailMessage()
        msg["Subject"] = f"[StockTrace] {event.summary}"
        msg["From"] = self.sender
        msg["To"] = ", ".join(self.recipients)
        msg.set_content(_format_message(event))
        try:
            with self._smtp_factory(self.host, self.port) as smtp:
                if self.use_tls:
                    smtp.starttls()
                if self.user:
                    smtp.login(self.user, self.password)
                smtp.send_message(msg)
            return True
        except Exception:
            logger.warning("email send failed", exc_info=True)
            return False


# ---------- Composite ---------- #

class CompositeChannel(NotificationChannel):
    """扇出多通道。個別失敗不影響其他；回傳「至少一個」成功。"""

    def __init__(self, channels: list[NotificationChannel]):
        self.channels = channels

    def send(self, event: NotificationEvent) -> bool:
        # 不用 any(...) 因為它會短路；明確收集所有結果再判斷
        results = [ch.send(event) for ch in self.channels]
        return any(results)


# ---------- Default channel resolution ---------- #

_CHANNEL_BUILDERS = {
    "web": WebNotificationChannel,
    "slack": SlackChannel,
    "line": LineChannel,
    "email": EmailChannel,
}


def _build_default() -> NotificationChannel:
    """根據 NOTIFICATION_CHANNELS env 組合預設通道（預設 'web'）。"""
    raw = os.environ.get("NOTIFICATION_CHANNELS", "web").lower()
    names = [n.strip() for n in raw.split(",") if n.strip()]
    channels: list[NotificationChannel] = []
    for n in names:
        builder = _CHANNEL_BUILDERS.get(n)
        if builder is None:
            logger.warning("unknown notification channel: %s", n)
            continue
        channels.append(builder())
    if not channels:
        channels = [WebNotificationChannel()]
    if len(channels) == 1:
        return channels[0]
    return CompositeChannel(channels)


_default: NotificationChannel | None = None


def get_default_channel() -> NotificationChannel:
    global _default
    if _default is None:
        _default = _build_default()
    return _default


def set_default_channel(channel: NotificationChannel) -> None:
    """測試或多通道整合時可注入替代實作。"""
    global _default
    _default = channel
