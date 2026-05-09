from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import EtfList
from app.schemas.etf import AumOverride, EtfCreate, EtfRead, EtfUpdate

router = APIRouter()


@router.get("", response_model=list[EtfRead])
def list_etfs(active_only: bool = False, db: Session = Depends(get_db)):
    stmt = select(EtfList).order_by(EtfList.etf_id)
    if active_only:
        stmt = stmt.where(EtfList.is_active.is_(True))
    return db.execute(stmt).scalars().all()


@router.post("", response_model=EtfRead, status_code=status.HTTP_201_CREATED)
def create_etf(payload: EtfCreate, db: Session = Depends(get_db)):
    if db.get(EtfList, payload.etf_id):
        raise HTTPException(409, f"ETF {payload.etf_id} already exists")
    entry = EtfList(**payload.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/{etf_id}", response_model=EtfRead)
def get_etf(etf_id: str, db: Session = Depends(get_db)):
    entry = db.get(EtfList, etf_id)
    if not entry:
        raise HTTPException(404, f"ETF {etf_id} not found")
    return entry


@router.patch("/{etf_id}", response_model=EtfRead)
def update_etf(etf_id: str, payload: EtfUpdate, db: Session = Depends(get_db)):
    entry = db.get(EtfList, etf_id)
    if not entry:
        raise HTTPException(404, f"ETF {etf_id} not found")
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(entry, key, value)
    db.commit()
    db.refresh(entry)
    return entry


@router.post("/{etf_id}/reset-crawler", status_code=status.HTTP_204_NO_CONTENT)
def reset_crawler(etf_id: str, db: Session = Depends(get_db)):
    """手動將 crawler_mode 從 playwright 降回 light，並把 fallback_count 歸零（規格 §6.3）。"""
    entry = db.get(EtfList, etf_id)
    if not entry:
        raise HTTPException(404, f"ETF {etf_id} not found")
    entry.crawler_mode = "light"
    entry.fallback_count = 0
    db.commit()


@router.post("/{etf_id}/aum", status_code=status.HTTP_204_NO_CONTENT)
def override_aum(etf_id: str, payload: AumOverride, db: Session = Depends(get_db)):
    """AUM 三層備援第二層：手動輸入 last_known_aum（規格 §6.4）。"""
    entry = db.get(EtfList, etf_id)
    if not entry:
        raise HTTPException(404, f"ETF {etf_id} not found")
    entry.last_known_aum = payload.aum
    db.commit()
