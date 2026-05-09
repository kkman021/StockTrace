from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.etf import AumOverride, EtfCreate, EtfRead, EtfUpdate

router = APIRouter()


@router.get("", response_model=list[EtfRead])
def list_etfs(active_only: bool = False, db: Session = Depends(get_db)):
    raise NotImplementedError("TODO: list ETF tracking entries")


@router.post("", response_model=EtfRead, status_code=201)
def create_etf(payload: EtfCreate, db: Session = Depends(get_db)):
    raise NotImplementedError("TODO: insert ETF entry")


@router.get("/{etf_id}", response_model=EtfRead)
def get_etf(etf_id: str, db: Session = Depends(get_db)):
    raise NotImplementedError("TODO: fetch single ETF")


@router.patch("/{etf_id}", response_model=EtfRead)
def update_etf(etf_id: str, payload: EtfUpdate, db: Session = Depends(get_db)):
    raise NotImplementedError("TODO: partial update ETF entry")


@router.post("/{etf_id}/reset-crawler", status_code=204)
def reset_crawler(etf_id: str, db: Session = Depends(get_db)):
    """手動將 crawler_mode 從 playwright 降回 light，並把 fallback_count 歸零。"""
    raise NotImplementedError("TODO: reset crawler mode + fallback_count")


@router.post("/{etf_id}/aum", status_code=204)
def override_aum(etf_id: str, payload: AumOverride, db: Session = Depends(get_db)):
    """AUM 三層備援的第二層：手動輸入 last_known_aum。"""
    raise NotImplementedError("TODO: write last_known_aum")
