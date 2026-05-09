import asyncio
import json
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from app.database import get_db
from app.models import SignalRecord
from app.schemas.signal import SignalRow

router = APIRouter()


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
    """SSE 即時推播：當 worker 寫入新的 signal_records 後透過 Redis pub/sub 廣播。

    TODO: 串接 Redis pub/sub channel `signals:new`，並由 notification.WebNotificationChannel 推送。
    目前僅維持心跳事件以保留前端連線骨架。
    """

    async def event_generator():
        while True:
            await asyncio.sleep(30)
            yield {"event": "ping", "data": json.dumps({"ts": "ping"})}

    return EventSourceResponse(event_generator())
