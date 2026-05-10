"""回測引擎（規格 §12）。

設計重點：
- 回測沙盒參數（breadth_thr / depth_thr / consec / holding_days）獨立於 system_config，
  所以 consensus_scores 既有的 consecutive_days 不能直接用，必須以使用者指定門檻重算。
- 觸發採「上升沿」邏輯：streak 第一次達門檻才視為觸發，之後 streak 持續不重複觸發；
  streak 中斷後再達門檻才會再觸發一次。
- 買入：觸發日後第一個有反推價的交易日（T+1 或更晚）
- 賣出：買入日往後第 holding_days 個交易日（買入日當第 1 天，賣出日為第 holding_days+1 天）
- 反推價缺失 → is_valid=False + invalid_reason
"""
from __future__ import annotations

import statistics
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import BacktestResult, BacktestRun, ConsensusScore
from app.services.prices import derive_close_price


# ---------- 觸發掃描 ---------- #

@dataclass
class Trigger:
    trigger_date: date
    stock_id: str
    stock_name: str | None
    breadth_score: Decimal
    depth_score: Decimal


def scan_triggers(
    db: Session,
    start: date,
    end: date,
    breadth_thr: float,
    depth_thr: float,
    consec: int,
    target_stocks: list[str] | None = None,
) -> list[Trigger]:
    """掃描 [start, end] 內所有上升沿觸發。

    為了正確判定 start 當天的 consec 連續性，會往前多載一段資料；
    日曆日的緩衝以 (consec-1) * 7 估算（極端漫長假期保險）。
    """
    buffer_days = max(0, consec - 1) * 7
    rows = db.execute(
        select(ConsensusScore)
        .where(
            ConsensusScore.date >= date.fromordinal(start.toordinal() - buffer_days),
            ConsensusScore.date <= end,
        )
        .order_by(ConsensusScore.stock_id, ConsensusScore.date)
    ).scalars().all()

    if target_stocks:
        target_set = {s.upper() for s in target_stocks}
        rows = [r for r in rows if r.stock_id.upper() in target_set]

    by_stock: dict[str, list[ConsensusScore]] = defaultdict(list)
    for r in rows:
        by_stock[r.stock_id].append(r)

    triggers: list[Trigger] = []
    for stock_id, scores in by_stock.items():
        scores.sort(key=lambda x: x.date)
        streak = 0
        triggered_in_current_streak = False
        for s in scores:
            hit = (
                float(s.breadth_score or 0) >= breadth_thr
                and float(s.depth_score or 0) >= depth_thr
            )
            if hit:
                streak += 1
                if (
                    streak >= consec
                    and not triggered_in_current_streak
                    and start <= s.date <= end
                ):
                    triggers.append(Trigger(
                        trigger_date=s.date,
                        stock_id=stock_id,
                        stock_name=s.stock_name,
                        breadth_score=s.breadth_score or Decimal("0"),
                        depth_score=s.depth_score or Decimal("0"),
                    ))
                    triggered_in_current_streak = True
            else:
                streak = 0
                triggered_in_current_streak = False

    triggers.sort(key=lambda t: (t.trigger_date, t.stock_id))
    return triggers


# ---------- 回測執行 ---------- #

@dataclass
class ResultRow:
    stock_id: str
    stock_name: str | None
    trigger_date: date
    buy_date: date
    buy_price: Decimal | None
    sell_date: date
    sell_price: Decimal | None
    return_rate: Decimal | None
    is_valid: bool
    invalid_reason: str | None
    breadth_score: Decimal
    depth_score: Decimal
    price_series: list[dict]


def _next_trading_day(trading_days: list[date], anchor: date) -> date | None:
    for d in trading_days:
        if d > anchor:
            return d
    return None


def _nth_trading_day_from(
    trading_days: list[date], start_inclusive: date, n: int
) -> date | None:
    started = False
    count = 0
    for d in trading_days:
        if not started:
            if d >= start_inclusive:
                started = True
            else:
                continue
        if started:
            count += 1
            if count == n:
                return d
    return None


def _all_trading_days(db: Session) -> list[date]:
    rows = db.execute(
        select(ConsensusScore.date).distinct().order_by(ConsensusScore.date)
    ).scalars().all()
    return list(rows)


def _evaluate_trigger(
    db: Session,
    trigger: Trigger,
    holding_days: int,
    trading_days: list[date],
) -> ResultRow:
    buy_anchor = _next_trading_day(trading_days, trigger.trigger_date)
    if buy_anchor is None:
        return ResultRow(
            stock_id=trigger.stock_id,
            stock_name=trigger.stock_name,
            trigger_date=trigger.trigger_date,
            buy_date=trigger.trigger_date,
            buy_price=None,
            sell_date=trigger.trigger_date,
            sell_price=None,
            return_rate=None,
            is_valid=False,
            invalid_reason="no_buy_trading_day",
            breadth_score=trigger.breadth_score,
            depth_score=trigger.depth_score,
            price_series=[],
        )

    sell_anchor = _nth_trading_day_from(trading_days, buy_anchor, holding_days + 1)
    buy_price = derive_close_price(db, trigger.stock_id, buy_anchor)

    if buy_price is None or buy_price <= 0:
        return ResultRow(
            stock_id=trigger.stock_id,
            stock_name=trigger.stock_name,
            trigger_date=trigger.trigger_date,
            buy_date=buy_anchor,
            buy_price=None,
            sell_date=sell_anchor or buy_anchor,
            sell_price=None,
            return_rate=None,
            is_valid=False,
            invalid_reason="missing_buy_price",
            breadth_score=trigger.breadth_score,
            depth_score=trigger.depth_score,
            price_series=[],
        )

    if sell_anchor is None:
        return ResultRow(
            stock_id=trigger.stock_id,
            stock_name=trigger.stock_name,
            trigger_date=trigger.trigger_date,
            buy_date=buy_anchor,
            buy_price=buy_price,
            sell_date=buy_anchor,
            sell_price=None,
            return_rate=None,
            is_valid=False,
            invalid_reason="insufficient_future_days",
            breadth_score=trigger.breadth_score,
            depth_score=trigger.depth_score,
            price_series=[],
        )

    sell_price = derive_close_price(db, trigger.stock_id, sell_anchor)

    series_dates = [d for d in trading_days if buy_anchor <= d <= sell_anchor]
    series: list[dict] = []
    for d in series_dates:
        p = derive_close_price(db, trigger.stock_id, d)
        if p is not None:
            series.append({"date": d.isoformat(), "price": float(p)})

    if sell_price is None or sell_price <= 0:
        return ResultRow(
            stock_id=trigger.stock_id,
            stock_name=trigger.stock_name,
            trigger_date=trigger.trigger_date,
            buy_date=buy_anchor,
            buy_price=buy_price,
            sell_date=sell_anchor,
            sell_price=None,
            return_rate=None,
            is_valid=False,
            invalid_reason="missing_sell_price",
            breadth_score=trigger.breadth_score,
            depth_score=trigger.depth_score,
            price_series=series,
        )

    return_rate = (sell_price - buy_price) / buy_price
    return ResultRow(
        stock_id=trigger.stock_id,
        stock_name=trigger.stock_name,
        trigger_date=trigger.trigger_date,
        buy_date=buy_anchor,
        buy_price=buy_price,
        sell_date=sell_anchor,
        sell_price=sell_price,
        return_rate=return_rate,
        is_valid=True,
        invalid_reason=None,
        breadth_score=trigger.breadth_score,
        depth_score=trigger.depth_score,
        price_series=series,
    )


def run_backtest(db: Session, run: BacktestRun) -> dict:
    """執行回測，將 ResultRow 寫入 backtest_results、更新 run.status。"""
    run.status = "running"
    db.commit()

    triggers = scan_triggers(
        db,
        run.start_date,
        run.end_date,
        float(run.breadth_threshold),
        float(run.depth_threshold),
        int(run.consecutive_days),
        target_stocks=run.target_stocks,
    )

    trading_days = _all_trading_days(db)

    valid_count = 0
    for t in triggers:
        row = _evaluate_trigger(db, t, run.holding_days, trading_days)
        db.add(BacktestResult(
            run_id=run.id,
            stock_id=row.stock_id,
            stock_name=row.stock_name,
            trigger_date=row.trigger_date,
            buy_date=row.buy_date,
            buy_price=row.buy_price,
            sell_date=row.sell_date,
            sell_price=row.sell_price,
            return_rate=row.return_rate,
            is_valid=row.is_valid,
            invalid_reason=row.invalid_reason,
            breadth_score=row.breadth_score,
            depth_score=row.depth_score,
            price_series=row.price_series or None,
        ))
        if row.is_valid:
            valid_count += 1

    run.status = "completed"
    run.completed_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "run_id": run.id,
        "triggers": len(triggers),
        "valid_results": valid_count,
        "invalid_results": len(triggers) - valid_count,
    }


# ---------- 統計摘要 ---------- #

def aggregate_summary(db: Session, run_id: int) -> list[dict]:
    """每檔股票的彙總統計。只計入 is_valid=True 的紀錄。"""
    results = db.execute(
        select(BacktestResult).where(BacktestResult.run_id == run_id)
    ).scalars().all()

    by_stock: dict[str, list[BacktestResult]] = defaultdict(list)
    for r in results:
        if r.is_valid and r.return_rate is not None:
            by_stock[r.stock_id].append(r)

    summary: list[dict] = []
    for stock_id, rows in by_stock.items():
        returns = [float(r.return_rate) for r in rows]
        breadths = [float(r.breadth_score) for r in rows if r.breadth_score is not None]
        depths = [float(r.depth_score) for r in rows if r.depth_score is not None]
        wins = sum(1 for r in returns if r > 0)
        summary.append({
            "stock_id": stock_id,
            "stock_name": rows[0].stock_name,
            "trigger_count": len(rows),
            "win_rate": wins / len(rows) if rows else 0.0,
            "avg_return": statistics.fmean(returns) if returns else 0.0,
            "max_return": max(returns) if returns else 0.0,
            "min_return": min(returns) if returns else 0.0,
            "avg_breadth": statistics.fmean(breadths) if breadths else 0.0,
            "avg_depth": statistics.fmean(depths) if depths else 0.0,
        })
    summary.sort(key=lambda x: x["avg_return"], reverse=True)
    return summary


def build_chart_payload(db: Session, run_id: int, stock_id: str) -> dict:
    """單檔股票的走勢圖：每次觸發一條 normalized 線（買入價=1.0）+ 平均粗線。"""
    rows = db.execute(
        select(BacktestResult).where(
            BacktestResult.run_id == run_id,
            BacktestResult.stock_id == stock_id,
            BacktestResult.is_valid.is_(True),
        )
    ).scalars().all()

    series: list[dict] = []
    normalized_by_offset: dict[int, list[float]] = defaultdict(list)

    for r in rows:
        if not r.price_series or not r.buy_price:
            continue
        buy = float(r.buy_price)
        line = []
        for offset, point in enumerate(r.price_series):
            try:
                p = float(point["price"])
            except (KeyError, TypeError, ValueError):
                continue
            ratio = p / buy
            line.append({"offset": offset, "ratio": ratio, "date": point.get("date")})
            normalized_by_offset[offset].append(ratio)
        series.append({"trigger_date": r.trigger_date.isoformat(), "line": line})

    avg_line = [
        {"offset": offset, "ratio": statistics.fmean(values)}
        for offset, values in sorted(normalized_by_offset.items())
    ]

    return {
        "stock_id": stock_id,
        "trigger_count": len(series),
        "series": series,
        "avg_line": avg_line,
    }
