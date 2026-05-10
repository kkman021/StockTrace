"""解析器抽象基底（規格 §22）。

每檔 ETF 一隻 Parser；當投信公告格式相近時，可共用 generic_table。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ParsedHolding:
    """單檔 ETF 解析後的標準化結果。"""

    holdings: list[dict] = field(default_factory=list)
    """ list[{stock_id: str, stock_name: str | None, shares_held: int, weight_pct: float | None}] """

    aum: int | None = None
    """ ETF 當日 AUM（元）。inline 模式由本 parser 取得；separate 模式留空，由另一頁 parser 補上。 """


class Parser(ABC):
    """每隻 Parser 必須實作 parse()。"""

    @abstractmethod
    def parse(self, html: str) -> ParsedHolding: ...

    def parse_aum_only(self, html: str) -> int | None:
        """若 ETF 採 aum_source='separate'，覆寫此方法解析另一頁 AUM。"""
        return None
