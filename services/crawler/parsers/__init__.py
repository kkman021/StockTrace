"""Parser registry。

預設使用 generic_table。當特定投信公告格式需要客製時，建立
parsers/{etf_id_lower}.py 並 export `Parser` 類別，再到 register() 註冊即可。
"""
from __future__ import annotations

from parsers.base import Parser
from parsers.generic_table import GenericTableParser


_REGISTRY: dict[str, type[Parser]] = {}


def register(etf_id: str, parser_cls: type[Parser]) -> None:
    _REGISTRY[etf_id.upper()] = parser_cls


def get_parser(etf_id: str) -> Parser:
    """取得指定 ETF 的 parser，找不到時退回 GenericTableParser。"""
    cls = _REGISTRY.get(etf_id.upper(), GenericTableParser)
    return cls()


# TODO: 實際對接投信網站後，視 HTML 結構是否需要客製，例如：
# from parsers.yuanta_00982a import YuantaActiveEtfParser
# register("00982A", YuantaActiveEtfParser)
