"""訊號偵測寫入（規格 §13.3）。

讀取 target_date 的 consensus_scores，套用 trigger_signal_tag / risk_tag，
將新觸發的訊號寫入 signal_records（唯一鍵 date+stock_id+signal_type）。
"""
from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models import ConsensusScore, SignalRecord, SystemConfig
from app.services.consensus import trigger_signal_tag
from app.services.reduction import risk_tag


SIGNAL_TYPE_ADD = "add"
SIGNAL_TYPE_REDUCE = "reduce"


def _read_thresholds(db: Session) -> dict[str, float | int]:
    rows = db.execute(select(SystemConfig)).scalars().all()
    raw = {r.key: r.value for r in rows}
    return {
        "breadth_thr": float(raw.get("breadth_threshold", 0.6)),
        "depth_thr": float(raw.get("depth_threshold", 0.6)),
        "consec_thr": int(raw.get("consecutive_days", 3)),
        "red_breadth_thr": float(raw.get("reduction_breadth_threshold", 0.6)),
        "red_consec_thr": int(raw.get("reduction_consecutive_days", 3)),
    }


def detect_date(db: Session, target_date: date) -> dict:
    """產生 target_date 的訊號紀錄，回傳統計資訊。

    去重：同 date+stock_id+signal_type 採 ON CONFLICT DO NOTHING；
    舊紀錄保留 notified_at，不覆寫。
    """
    thr = _read_thresholds(db)

    rows = db.execute(
        select(ConsensusScore).where(ConsensusScore.date == target_date)
    ).scalars().all()

    new_signals = 0
    for row in rows:
        breadth = float(row.breadth_score or 0)
        depth = float(row.depth_score or 0)
        consec = int(row.consecutive_days or 0)

        add_tag = trigger_signal_tag(
            breadth, depth, consec,
            thr["breadth_thr"], thr["depth_thr"], thr["consec_thr"],
        )
        if add_tag is not None:
            stmt = pg_insert(SignalRecord).values(
                date=target_date,
                stock_id=row.stock_id,
                stock_name=row.stock_name,
                signal_type=SIGNAL_TYPE_ADD,
                signal_tag=add_tag,
                breadth_score=row.breadth_score,
                depth_score=row.depth_score,
                consecutive_days=consec,
            ).on_conflict_do_nothing(index_elements=["date", "stock_id", "signal_type"])
            result = db.execute(stmt)
            if result.rowcount:
                new_signals += 1

        red_breadth = float(row.reduction_breadth or 0)
        red_consec = int(row.reduction_consec or 0)
        red_tag = risk_tag(red_breadth, thr["red_breadth_thr"], red_consec, thr["red_consec_thr"])
        if red_tag is not None:
            stmt = pg_insert(SignalRecord).values(
                date=target_date,
                stock_id=row.stock_id,
                stock_name=row.stock_name,
                signal_type=SIGNAL_TYPE_REDUCE,
                signal_tag=red_tag,
                breadth_score=row.reduction_breadth,
                depth_score=None,
                consecutive_days=red_consec,
            ).on_conflict_do_nothing(index_elements=["date", "stock_id", "signal_type"])
            result = db.execute(stmt)
            if result.rowcount:
                new_signals += 1

    db.commit()
    return {"date": str(target_date), "new_signals": new_signals, "consensus_rows_scanned": len(rows)}
