"""通知任務（規格 §13、§21）。"""
from celery_app import celery_app


@celery_app.task(name="tasks.notify.send_notifications")
def send_notifications(target_date: str, notification_type: str = "realtime") -> dict:
    """推播通知。
    - notification_type='realtime': 18:30 後即時推播當日新訊號
    - notification_type='summary': 08:30 早盤摘要
    """
    raise NotImplementedError("TODO: query signal_records, dispatch via NotificationChannel(s)")


@celery_app.task(name="tasks.notify.generate_morning_summary")
def generate_morning_summary() -> dict:
    """08:30 排程：產出昨日所有有效訊號摘要 + 連續加碼排行 Top 5。"""
    raise NotImplementedError("TODO")
