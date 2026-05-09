"""分析任務的 DB 編排（規格 §8、§9、§14）。

負責：
- 讀取 target_date 與 target_date-1 的 holding_records
- 反推每檔股票的收盤價（從 weight_pct × aum / shares_held）
- 呼叫 aggregation.aggregate 計算分數
- 計算 consecutive_days（沿 consensus_scores 往回走 sliding_window 筆）
- Upsert 到 consensus_scores

除權息資料來源（規格 §5.2）尚未串接，目前 stock_dividend_ratio 一律 0。
"""
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models import ConsensusScore, EtfList, HoldingRecord, SystemConfig
from app.services.aggregation import HoldingDelta, StockConsensus, aggregate


def load_config(db: Session) -> dict[str, str]:
    """讀取 system_config 全部門檻參數。"""
    rows = db.execute(select(SystemConfig)).scalars().all()
    return {r.key: r.value for r in rows}


def _derive_close_price(weight_pct: Decimal | None, aum: int | None, shares_held: int) -> Decimal:
    """從持股公告反推收盤價（規格未提供獨立 daily_prices 表）。

    收盤價 ≈ ETF AUM × weight_pct / 100 / shares_held
    資料缺失時回傳 0（深度分數會被低估，是已知簡化）。
    """
    if not weight_pct or not aum or shares_held <= 0:
        return Decimal("0")
    return Decimal(aum) * Decimal(weight_pct) / Decimal(100) / Decimal(shares_held)


def build_deltas(
    db: Session,
    target_date: date,
) -> tuple[list[HoldingDelta], dict[str, int | None]]:
    """從 holding_records 拼出 (deltas, aum_today_per_etf)。"""
    yesterday = target_date - timedelta(days=1)

    today_rows = db.execute(
        select(HoldingRecord).where(HoldingRecord.date == target_date)
    ).scalars().all()
    yest_rows = db.execute(
        select(HoldingRecord).where(HoldingRecord.date == yesterday)
    ).scalars().all()

    aum_today: dict[str, int | None] = {}
    aum_yesterday: dict[str, int | None] = {}
    today_idx: dict[tuple[str, str], HoldingRecord] = {}
    yest_idx: dict[tuple[str, str], HoldingRecord] = {}

    for r in today_rows:
        today_idx[(r.etf_id, r.stock_id)] = r
        aum_today.setdefault(r.etf_id, r.aum)
    for r in yest_rows:
        yest_idx[(r.etf_id, r.stock_id)] = r
        aum_yesterday.setdefault(r.etf_id, r.aum)

    keys = set(today_idx) | set(yest_idx)
    deltas: list[HoldingDelta] = []
    for etf_id, stock_id in keys:
        today_row = today_idx.get((etf_id, stock_id))
        yest_row = yest_idx.get((etf_id, stock_id))
        ref = today_row or yest_row  # 用今日資料推導收盤價，清倉時退回昨日
        close_price = _derive_close_price(
            ref.weight_pct if ref else None,
            ref.aum if ref else None,
            ref.shares_held if ref else 0,
        )
        deltas.append(
            HoldingDelta(
                etf_id=etf_id,
                stock_id=stock_id,
                yesterday_shares=yest_row.shares_held if yest_row else 0,
                today_shares=today_row.shares_held if today_row else 0,
                aum_today=aum_today.get(etf_id),
                aum_yesterday=aum_yesterday.get(etf_id),
                close_price=close_price,
                stock_dividend_ratio=Decimal("0"),  # TODO: integrate dividend feed
            )
        )

    return deltas, aum_today


def count_active_etfs(db: Session, target_date: date) -> int:
    """N = 當日 is_active=true AND 當日有持股資料的 ETF 數量（規格 §7.3）。"""
    sub = (
        select(HoldingRecord.etf_id)
        .where(HoldingRecord.date == target_date)
        .distinct()
    )
    rows = db.execute(
        select(EtfList.etf_id).where(EtfList.is_active.is_(True), EtfList.etf_id.in_(sub))
    ).scalars().all()
    return len(rows)


def compute_prior_consecutive_days(
    db: Session,
    stock_id: str,
    target_date: date,
    side: str,
    sliding_window: int,
) -> int:
    """往回看最多 sliding_window 筆 consensus_scores（不含 target_date 當日）。

    沿 date desc 走，遇到不符合條件即中斷。
    side='accumulate'：accumulate_etf_count > 0
    side='reduce'：reduction_etf_count > 0
    """
    rows = db.execute(
        select(ConsensusScore)
        .where(
            ConsensusScore.stock_id == stock_id,
            ConsensusScore.date < target_date,
        )
        .order_by(ConsensusScore.date.desc())
        .limit(sliding_window)
    ).scalars().all()

    consec = 0
    for row in rows:
        active = (
            (row.accumulate_etf_count or 0) > 0
            if side == "accumulate"
            else (row.reduction_etf_count or 0) > 0
        )
        if not active:
            break
        consec += 1
    return consec


def upsert_consensus_row(
    db: Session,
    target_date: date,
    consensus: StockConsensus,
    consec_acc: int,
    consec_red: int,
    cfg: dict[str, str],
) -> None:
    stmt = pg_insert(ConsensusScore).values(
        date=target_date,
        stock_id=consensus.stock_id,
        breadth_score=consensus.breadth_score,
        depth_score=consensus.depth_score,
        accumulate_etf_count=consensus.accumulate_etf_count,
        total_amount=consensus.total_active_amount,
        consecutive_days=consec_acc,
        signal_tag=consensus.signal_tag,
        reduction_breadth=consensus.reduction_breadth,
        reduction_etf_count=consensus.reduction_etf_count,
        reduction_consec=consec_red,
        param_breadth_thr=cfg["breadth_threshold"],
        param_depth_thr=cfg["depth_threshold"],
        param_consec_days=cfg["consecutive_days"],
        param_red_breadth=cfg["reduction_breadth_threshold"],
        param_red_consec=cfg["reduction_consecutive_days"],
        n_etfs=consensus.n_etfs,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["date", "stock_id"],
        set_={
            "breadth_score": stmt.excluded.breadth_score,
            "depth_score": stmt.excluded.depth_score,
            "accumulate_etf_count": stmt.excluded.accumulate_etf_count,
            "total_amount": stmt.excluded.total_amount,
            "consecutive_days": stmt.excluded.consecutive_days,
            "signal_tag": stmt.excluded.signal_tag,
            "reduction_breadth": stmt.excluded.reduction_breadth,
            "reduction_etf_count": stmt.excluded.reduction_etf_count,
            "reduction_consec": stmt.excluded.reduction_consec,
            "n_etfs": stmt.excluded.n_etfs,
        },
    )
    db.execute(stmt)


def analyze_date(db: Session, target_date: date) -> dict:
    """整體編排：讀取 → 彙總 → 寫入 consensus_scores。"""
    cfg = load_config(db)
    breadth_thr = float(cfg.get("breadth_threshold", 0.6))
    depth_thr = float(cfg.get("depth_threshold", 0.6))
    sliding_window = int(cfg.get("sliding_window", 5))

    deltas, aum_today_per_etf = build_deltas(db, target_date)
    n_etfs = count_active_etfs(db, target_date)
    total_aum = sum(v for v in aum_today_per_etf.values() if v is not None)

    if not deltas or n_etfs == 0:
        return {"date": str(target_date), "n_etfs": n_etfs, "rows_written": 0}

    consensus_rows = aggregate(deltas, n_etfs, total_aum, breadth_thr, depth_thr)

    for row in consensus_rows:
        consec_acc = (
            1 + compute_prior_consecutive_days(db, row.stock_id, target_date, "accumulate", sliding_window)
            if row.accumulate_etf_count > 0
            else 0
        )
        consec_red = (
            1 + compute_prior_consecutive_days(db, row.stock_id, target_date, "reduce", sliding_window)
            if row.reduction_etf_count > 0
            else 0
        )
        upsert_consensus_row(db, target_date, row, consec_acc, consec_red, cfg)

    db.commit()
    return {"date": str(target_date), "n_etfs": n_etfs, "rows_written": len(consensus_rows)}
