from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import BacktestRun
from app.schemas.backtest import BacktestCreate, BacktestRunRead, BacktestSummaryRow
from app.services import backtest as backtest_service

router = APIRouter()


@router.post("", response_model=BacktestRunRead, status_code=201)
def create_backtest(payload: BacktestCreate, db: Session = Depends(get_db)):
    """建立回測任務並同步執行。

    回測屬於使用者觸發的一次性沙盒運算，沒有排程依賴；
    為避免從 web 端設定 Celery client，這裡採同步呼叫，
    回應時 status 已是 'completed' 或 'failed'，前端不需輪詢。
    """
    if payload.start_date > payload.end_date:
        raise HTTPException(400, "start_date must be <= end_date")

    run = BacktestRun(
        start_date=payload.start_date,
        end_date=payload.end_date,
        holding_days=payload.holding_days,
        breadth_threshold=Decimal(str(payload.breadth_threshold)),
        depth_threshold=Decimal(str(payload.depth_threshold)),
        consecutive_days=payload.consecutive_days,
        target_stocks=payload.target_stocks,
        status="pending",
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    backtest_service.run_backtest(db, run)
    db.refresh(run)
    return run


@router.get("", response_model=list[BacktestRunRead])
def list_backtests(db: Session = Depends(get_db)):
    rows = db.execute(
        select(BacktestRun).order_by(BacktestRun.created_at.desc())
    ).scalars().all()
    return rows


@router.get("/{run_id}", response_model=BacktestRunRead)
def get_backtest(run_id: int, db: Session = Depends(get_db)):
    run = db.get(BacktestRun, run_id)
    if run is None:
        raise HTTPException(404, "backtest run not found")
    return run


@router.get("/{run_id}/summary", response_model=list[BacktestSummaryRow])
def get_backtest_summary(run_id: int, db: Session = Depends(get_db)):
    if db.get(BacktestRun, run_id) is None:
        raise HTTPException(404, "backtest run not found")
    return backtest_service.aggregate_summary(db, run_id)


@router.get("/{run_id}/chart/{stock_id}")
def get_backtest_chart(run_id: int, stock_id: str, db: Session = Depends(get_db)):
    if db.get(BacktestRun, run_id) is None:
        raise HTTPException(404, "backtest run not found")
    return backtest_service.build_chart_payload(db, run_id, stock_id)
