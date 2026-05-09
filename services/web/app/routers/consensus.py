from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ConsensusScore
from app.schemas.consensus import ConsensusRow, ReductionRow

router = APIRouter()


def _latest_date(db: Session) -> date | None:
    return db.execute(
        select(ConsensusScore.date).order_by(ConsensusScore.date.desc()).limit(1)
    ).scalar_one_or_none()


@router.get("", response_model=list[ConsensusRow])
def latest_consensus(
    limit: int = 50,
    signal_only: bool = False,
    db: Session = Depends(get_db),
):
    """最新一日的加碼共識排行表（依廣度+深度遞減排序）。"""
    target = _latest_date(db)
    if target is None:
        return []
    stmt = (
        select(ConsensusScore)
        .where(ConsensusScore.date == target)
        .order_by(
            ConsensusScore.breadth_score.desc().nulls_last(),
            ConsensusScore.depth_score.desc().nulls_last(),
        )
        .limit(limit)
    )
    if signal_only:
        stmt = stmt.where(ConsensusScore.signal_tag.is_not(None))
    return db.execute(stmt).scalars().all()


@router.get("/reduction", response_model=list[ReductionRow])
def latest_reduction(
    limit: int = 50,
    risk_only: bool = False,
    db: Session = Depends(get_db),
):
    """最新一日的減碼風險警示列表。"""
    target = _latest_date(db)
    if target is None:
        return []
    stmt = (
        select(ConsensusScore)
        .where(ConsensusScore.date == target)
        .where(ConsensusScore.reduction_etf_count > 0)
        .order_by(ConsensusScore.reduction_breadth.desc().nulls_last())
        .limit(limit)
    )
    if risk_only:
        stmt = stmt.where(ConsensusScore.risk_tag.is_not(None))
    return db.execute(stmt).scalars().all()


@router.get("/{target_date}", response_model=list[ConsensusRow])
def consensus_by_date(target_date: date, db: Session = Depends(get_db)):
    stmt = (
        select(ConsensusScore)
        .where(ConsensusScore.date == target_date)
        .order_by(
            ConsensusScore.breadth_score.desc().nulls_last(),
            ConsensusScore.depth_score.desc().nulls_last(),
        )
    )
    return db.execute(stmt).scalars().all()


@router.get("/stock/{stock_id}", response_model=list[ConsensusRow])
def consensus_by_stock(stock_id: str, days: int = 90, db: Session = Depends(get_db)):
    """單檔股票歷史共識分數走勢（規格 v1.3 個股深度頁面用，§29.2）。"""
    stmt = (
        select(ConsensusScore)
        .where(ConsensusScore.stock_id == stock_id)
        .order_by(ConsensusScore.date.desc())
        .limit(days)
    )
    return db.execute(stmt).scalars().all()
