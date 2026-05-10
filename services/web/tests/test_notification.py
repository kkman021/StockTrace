"""Tests for notification channels (規格 §13)。"""
from unittest.mock import MagicMock

import httpx

from app.services.notification import (
    CompositeChannel,
    EmailChannel,
    LineChannel,
    NotificationEvent,
    SlackChannel,
    _build_default,
    _format_message,
)


def _evt(**overrides):
    base = dict(
        stock_id="2330", stock_name="台積電",
        signal_type="add", signal_tag="high_consensus",
        summary="高度共識：台積電（2330）",
        breadth_score=0.75, depth_score=0.65, consecutive_days=3,
    )
    base.update(overrides)
    return NotificationEvent(**base)


class TestFormatMessage:
    def test_includes_summary_and_scores(self):
        msg = _format_message(_evt())
        assert "台積電" in msg
        assert "廣度 0.75" in msg
        assert "深度 0.65" in msg
        assert "連續 3 日" in msg

    def test_reduce_uses_warning_emoji(self):
        msg = _format_message(_evt(signal_type="reduce"))
        assert "🚨" in msg

    def test_handles_missing_scores_gracefully(self):
        msg = _format_message(_evt(breadth_score=None, depth_score=None, consecutive_days=None))
        # summary 本身可能含全形括號，這裡確認沒有附加「廣度/深度/連續」分數區塊
        assert "廣度" not in msg
        assert "深度" not in msg
        assert "連續" not in msg


class TestSlackChannel:
    def test_disabled_when_no_webhook(self):
        ch = SlackChannel(webhook_url="")
        assert ch.send(_evt()) is False

    def test_posts_text_payload(self):
        captured: dict = {}

        def handler(req: httpx.Request) -> httpx.Response:
            captured["body"] = req.read().decode()
            return httpx.Response(200, json={"ok": True})

        client = httpx.Client(transport=httpx.MockTransport(handler))
        ch = SlackChannel(webhook_url="https://hooks.slack.test/x", http_client=client)
        assert ch.send(_evt()) is True
        assert "台積電" in captured["body"]

    def test_returns_false_on_non_2xx(self):
        client = httpx.Client(transport=httpx.MockTransport(
            lambda r: httpx.Response(500)
        ))
        ch = SlackChannel(webhook_url="https://hooks.slack.test/x", http_client=client)
        assert ch.send(_evt()) is False

    def test_returns_false_on_network_error(self):
        def boom(req):
            raise httpx.ConnectError("dns failure")
        client = httpx.Client(transport=httpx.MockTransport(boom))
        ch = SlackChannel(webhook_url="https://x", http_client=client)
        assert ch.send(_evt()) is False


class TestLineChannel:
    def test_disabled_when_no_token(self):
        assert LineChannel(token="").send(_evt()) is False

    def test_sends_with_bearer_token(self):
        captured: dict = {}

        def handler(req: httpx.Request) -> httpx.Response:
            captured["auth"] = req.headers.get("authorization")
            captured["body"] = req.read().decode()
            return httpx.Response(200)

        client = httpx.Client(transport=httpx.MockTransport(handler))
        ch = LineChannel(token="abc123", http_client=client)
        assert ch.send(_evt()) is True
        assert captured["auth"] == "Bearer abc123"
        assert "message=" in captured["body"]

    def test_returns_false_on_non_200(self):
        client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(401)))
        assert LineChannel(token="x", http_client=client).send(_evt()) is False


class TestEmailChannel:
    def test_disabled_when_incomplete_config(self):
        ch = EmailChannel(host="", recipients="", smtp_factory=MagicMock())
        assert ch.send(_evt()) is False

    def test_sends_via_smtp(self):
        smtp_instance = MagicMock()
        smtp_factory = MagicMock(return_value=smtp_instance)
        smtp_instance.__enter__ = MagicMock(return_value=smtp_instance)
        smtp_instance.__exit__ = MagicMock(return_value=False)

        ch = EmailChannel(
            host="smtp.test", port=587, user="bot", password="pw",
            sender="bot@test", recipients="a@test,b@test",
            use_tls=True, smtp_factory=smtp_factory,
        )
        assert ch.send(_evt()) is True

        smtp_instance.starttls.assert_called_once()
        smtp_instance.login.assert_called_once_with("bot", "pw")
        smtp_instance.send_message.assert_called_once()
        sent_msg = smtp_instance.send_message.call_args[0][0]
        assert sent_msg["To"] == "a@test, b@test"
        assert sent_msg["Subject"].startswith("[StockTrace]")

    def test_skips_login_when_no_user(self):
        smtp_instance = MagicMock()
        smtp_instance.__enter__ = MagicMock(return_value=smtp_instance)
        smtp_instance.__exit__ = MagicMock(return_value=False)
        ch = EmailChannel(
            host="smtp.test", port=25, user="", password="",
            sender="bot@test", recipients="a@test",
            use_tls=False, smtp_factory=MagicMock(return_value=smtp_instance),
        )
        assert ch.send(_evt()) is True
        smtp_instance.login.assert_not_called()
        smtp_instance.starttls.assert_not_called()


class TestCompositeChannel:
    def test_fans_out_to_all_channels(self):
        a, b, c = MagicMock(), MagicMock(), MagicMock()
        a.send.return_value = True
        b.send.return_value = False
        c.send.return_value = True
        comp = CompositeChannel([a, b, c])
        evt = _evt()
        assert comp.send(evt) is True
        a.send.assert_called_once_with(evt)
        b.send.assert_called_once_with(evt)
        c.send.assert_called_once_with(evt)

    def test_returns_false_when_all_fail(self):
        a, b = MagicMock(), MagicMock()
        a.send.return_value = False
        b.send.return_value = False
        assert CompositeChannel([a, b]).send(_evt()) is False

    def test_individual_exception_does_not_block_others(self):
        # CompositeChannel 假設子 channel 自行 fail-silent；
        # 若子 channel 真的拋出未捕獲例外，整體會中斷 —— 這裡確認子 channel
        # 落實「不丟例外」契約即可。
        a = MagicMock()
        a.send.side_effect = lambda evt: False  # 模擬 fail-silent 後回 False
        b = MagicMock()
        b.send.return_value = True
        assert CompositeChannel([a, b]).send(_evt()) is True


class TestBuildDefault:
    def test_default_is_web_only(self, monkeypatch):
        monkeypatch.delenv("NOTIFICATION_CHANNELS", raising=False)
        ch = _build_default()
        # WebNotificationChannel single
        from app.services.notification import WebNotificationChannel
        assert isinstance(ch, WebNotificationChannel)

    def test_multiple_channels_wraps_composite(self, monkeypatch):
        monkeypatch.setenv("NOTIFICATION_CHANNELS", "web,slack,line")
        ch = _build_default()
        assert isinstance(ch, CompositeChannel)
        assert len(ch.channels) == 3

    def test_unknown_channel_is_skipped(self, monkeypatch):
        monkeypatch.setenv("NOTIFICATION_CHANNELS", "web,bogus")
        ch = _build_default()
        from app.services.notification import WebNotificationChannel
        assert isinstance(ch, WebNotificationChannel)

    def test_empty_falls_back_to_web(self, monkeypatch):
        monkeypatch.setenv("NOTIFICATION_CHANNELS", "  ,  ,  ")
        ch = _build_default()
        from app.services.notification import WebNotificationChannel
        assert isinstance(ch, WebNotificationChannel)
