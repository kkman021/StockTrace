"""每檔 ETF 一隻 Parser（規格 §30 已知限制）。

慣例：parsers/{etf_id}.py 提供 `parse(html: str) -> ParsedHolding`。
config/etf_parsers.json 記錄 etf_id → parser module 的對應。
"""
from dataclasses import dataclass, field


@dataclass
class ParsedHolding:
    holdings: list[dict] = field(default_factory=list)  # [{stock_id, shares_held, weight_pct}]
    aum: int | None = None


def parse(html: str) -> ParsedHolding:
    raise NotImplementedError("TODO: provide a parser per ETF under parsers/{etf_id}.py")
