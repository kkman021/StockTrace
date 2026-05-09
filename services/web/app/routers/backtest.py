from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.backtest import BacktestCreate, BacktestRunRead, BacktestSummaryRow

router = APIRouter()


@router.post("", response_model=BacktestRunRead, status_code=201)
def create_backtest(payload: BacktestCreate, db: Session = Depends(get_db)):
    """建立回測任務，發送到 Celery。回傳 run_id 給前端輪詢。"""
    raise NotImplementedError("TODO: insert backtest_runs + dispatch celery task")


@router.get("", response_model=list[BacktestRunRead])
def list_backtests(db: Session = Depends(get_db)):
    raise NotImplementedError("TODO: list backtest_runs")


@router.get("/{run_id}", response_model=BacktestRunRead)
def get_backtest(run_id: int, db: Session = Depends(get_db)):
    raise NotImplementedError("TODO: fetch run record")


@router.get("/{run_id}/summary", response_model=list[BacktestSummaryRow])
def get_backtest_summary(run_id: int, db: Session = Depends(get_db)):
    raise NotImplementedError("TODO: aggregate backtest_results into summary")


@router.get("/{run_id}/chart/{stock_id}")
def get_backtest_chart(run_id: int, stock_id: str, db: Session = Depends(get_db)):
    """單檔走勢圖資料：每次觸發一條細線 + 平均粗線。"""
    raise NotImplementedError("TODO: build chart payload from price_series JSONB")
