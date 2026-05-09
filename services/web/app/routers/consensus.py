from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.consensus import ConsensusRow, ReductionRow

router = APIRouter()


@router.get("", response_model=list[ConsensusRow])
def latest_consensus(db: Session = Depends(get_db)):
    """回傳最新一日的加碼共識排行表。"""
    raise NotImplementedError("TODO: query latest consensus_scores rows")


@router.get("/reduction", response_model=list[ReductionRow])
def latest_reduction(db: Session = Depends(get_db)):
    """回傳最新一日的減碼風險警示列表。"""
    raise NotImplementedError("TODO: query latest reduction rows")


@router.get("/{target_date}", response_model=list[ConsensusRow])
def consensus_by_date(target_date: date, db: Session = Depends(get_db)):
    raise NotImplementedError("TODO: query consensus_scores by date")


@router.get("/stock/{stock_id}", response_model=list[ConsensusRow])
def consensus_by_stock(stock_id: str, db: Session = Depends(get_db)):
    """單檔股票歷史共識分數走勢（v1.3 詳情頁用）。"""
    raise NotImplementedError("TODO: query history series for a stock")
