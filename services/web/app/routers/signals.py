import asyncio
import json
import logging
import os
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from app.database import get_db
from app.models import SignalRecord
from app.schemas.signal import SignalRow
from app.services.notification import SIGNAL_CHANNEL

logger = logging.getLogger(__name__)
router = APIRouter()


REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")


@router.get("", response_model=list[SignalRow])
def list_signals(
    target_date: date | None = Query(default=None, alias="date"),
    signal_type: str | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """查詢 signal_records，預設依時間倒序。"""
    stmt = select(SignalRecord).order_by(
        SignalRecord.date.desc(), SignalRecord.created_at.desc()
    )
    if target_date is not None:
        stmt = stmt.where(SignalRecord.date == target_date)
    if signal_type is not None:
        stmt = stmt.where(SignalRecord.signal_type == signal_type)
    stmt = stmt.limit(limit)
    return db.execute(stmt).scalars().all()


@router.get("/stream")
async def stream_signals():
    """SSE 即時推播：訂閱 Redis pub/sub channel `signals:new`（規格 §13、§23.2）。

    任何 signal_detector.detect_date 寫入新訊號的事件都會推到這個串流，
    前端 useSignalNotifications 收到後轉為 Web Notification。
    """
    return EventSourceResponse(_event_generator(), ping=20)


async def _event_generator():
    import redis.asyncio as aioredis

    client = aioredis.from_url(REDIS_URL, decode_responses=True)
    pubsub = client.pubsub()
    try:
        await pubsub.subscribe(SIGNAL_CHANNEL)
        while True:
            try:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=20.0
                )
            except asyncio.CancelledError:
                break
            if message is None:
                continue
            data = message.get("data")
            if not data:
                continue
            yield {"event": "signal", "data": data}
    except Exception:
        logger.exception("SSE subscriber error")
    finally:
        try:
            await pubsub.unsubscribe(SIGNAL_CHANNEL)
            await pubsub.aclose()
            await client.aclose()
        except Exception:
            pass
