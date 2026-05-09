from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SystemConfig
from app.schemas.config import ThresholdConfig, ThresholdConfigPatch

router = APIRouter()


# 預期 system_config 中存在的鍵；缺鍵時回退到預設值（與遷移檔的 INSERT 同步）
KEY_DEFAULTS: dict[str, str] = {
    "breadth_threshold": "0.6",
    "depth_threshold": "0.6",
    "consecutive_days": "3",
    "sliding_window": "5",
    "reduction_breadth_threshold": "0.6",
    "reduction_consecutive_days": "3",
}


def _read_all(db: Session) -> dict[str, str]:
    rows = db.execute(select(SystemConfig)).scalars().all()
    return {r.key: r.value for r in rows}


def _coerce(values: dict[str, str]) -> ThresholdConfig:
    return ThresholdConfig(
        breadth_threshold=float(values.get("breadth_threshold", KEY_DEFAULTS["breadth_threshold"])),
        depth_threshold=float(values.get("depth_threshold", KEY_DEFAULTS["depth_threshold"])),
        consecutive_days=int(values.get("consecutive_days", KEY_DEFAULTS["consecutive_days"])),
        sliding_window=int(values.get("sliding_window", KEY_DEFAULTS["sliding_window"])),
        reduction_breadth_threshold=float(values.get(
            "reduction_breadth_threshold", KEY_DEFAULTS["reduction_breadth_threshold"]
        )),
        reduction_consecutive_days=int(values.get(
            "reduction_consecutive_days", KEY_DEFAULTS["reduction_consecutive_days"]
        )),
    )


@router.get("", response_model=ThresholdConfig)
def get_thresholds(db: Session = Depends(get_db)):
    """從 system_config 動態讀取門檻參數（規格 §11、§24）。"""
    return _coerce(_read_all(db))


@router.patch("", response_model=ThresholdConfig)
def update_thresholds(payload: ThresholdConfigPatch, db: Session = Depends(get_db)):
    """更新門檻參數，runtime 即時生效（規格 §11、§24）。歷史訊號不重算。"""
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        entry = db.get(SystemConfig, key)
        str_value = str(value)
        if entry:
            entry.value = str_value
        else:
            db.add(SystemConfig(key=key, value=str_value))
    db.commit()
    return _coerce(_read_all(db))
