"""Celery Beat 排程（規格 §14、§21.2）。"""
from celery.schedules import crontab

beat_schedule = {
    "morning-summary": {
        "task": "tasks.notify.generate_morning_summary",
        "schedule": crontab(hour=8, minute=30),
    },
    "crawl-1830": {
        "task": "tasks.crawl.crawl_all_etfs",
        "schedule": crontab(hour=18, minute=30),
    },
    "crawl-1930": {
        "task": "tasks.crawl.crawl_all_etfs",
        "schedule": crontab(hour=19, minute=30),
        "kwargs": {"retry_missing_only": True},
    },
    "crawl-2100": {
        "task": "tasks.crawl.crawl_all_etfs",
        "schedule": crontab(hour=21, minute=0),
        "kwargs": {"retry_missing_only": True},
    },
}
