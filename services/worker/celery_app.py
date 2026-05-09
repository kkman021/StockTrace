import os

from celery import Celery

from celeryconfig import beat_schedule

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "etf_radar",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "tasks.crawl",
        "tasks.analyze",
        "tasks.notify",
        "tasks.backtest",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Taipei",
    enable_utc=False,
    beat_schedule=beat_schedule,
)
