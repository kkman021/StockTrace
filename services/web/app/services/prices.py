"""股價反推工具（規格無獨立 daily_prices 表，由持股資料反推）。

收盤價推估：對該日所有持有此股票的 ETF 計算
  ETF AUM × weight_pct / 100 / shares_held
取平均值（過濾掉缺資料的 ETF）。

> 同一檔股票被 N 檔 ETF 持有時，理論上各 ETF 反推應一致；
> 取平均可吸收四捨五入造成的細微差異。
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import HoldingRecord


def derive_close_price(
    db: Session,
    stock_id: str,
    target_date: date,
) -> Decimal | None:
    """回傳指定股票於該日的反推收盤價，無法計算時回傳 None。"""
    rows = db.execute(
        select(HoldingRecord).where(
            HoldingRecord.stock_id == stock_id,
            HoldingRecord.date == target_date,
        )
    ).scalars().all()

    estimates: list[Decimal] = []
    for r in rows:
        if not r.weight_pct or not r.aum or r.shares_held <= 0:
            continue
        estimates.append(
            Decimal(r.aum) * Decimal(r.weight_pct) / Decimal(100) / Decimal(r.shares_held)
        )

    if not estimates:
        return None
    return sum(estimates) / Decimal(len(estimates))


def derive_close_price_series(
    db: Session,
    stock_id: str,
    dates: list[date],
) -> dict[date, Decimal]:
    """批量取得多日反推價，缺資料的日子不會出現在結果中。"""
    out: dict[date, Decimal] = {}
    for d in dates:
        price = derive_close_price(db, stock_id, d)
        if price is not None:
            out[d] = price
    return out
