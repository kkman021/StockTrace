from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.config import ThresholdConfig, ThresholdConfigPatch

router = APIRouter()


@router.get("", response_model=ThresholdConfig)
def get_thresholds(db: Session = Depends(get_db)):
    """從 system_config 動態讀取所有門檻參數。"""
    raise NotImplementedError("TODO: read keys from system_config")


@router.patch("", response_model=ThresholdConfig)
def update_thresholds(payload: ThresholdConfigPatch, db: Session = Depends(get_db)):
    """動態更新門檻參數，runtime 即時生效（不需重啟）。歷史訊號不重算。"""
    raise NotImplementedError("TODO: upsert keys in system_config")
