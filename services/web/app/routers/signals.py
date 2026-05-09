import asyncio
import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from app.database import get_db

router = APIRouter()


@router.get("")
def list_signals(db: Session = Depends(get_db)):
    raise NotImplementedError("TODO: query signal_records")


@router.get("/stream")
async def stream_signals():
    """SSE 即時推播：當 worker 寫入新的 signal_records 後透過 Redis pub/sub 廣播。"""

    async def event_generator():
        # TODO: subscribe to Redis pub/sub channel `signals:new`
        while True:
            await asyncio.sleep(30)
            yield {"event": "ping", "data": json.dumps({"ts": "ping"})}

    return EventSourceResponse(event_generator())
