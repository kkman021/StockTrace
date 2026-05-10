"""通用 Taiwan ETF 持股公告表格 Parser。

處理常見格式：
- <table> 含表頭關鍵字（股票代號 / 代碼 / Stock + 股數 / Shares + 比例 / Weight）
- 數字含千分位逗號、百分號
- AUM 通常以 `基金規模 NT$ X,XXX,XXX,XXX` 或類似字串出現於頁面任處
"""
from __future__ import annotations

import re

from bs4 import BeautifulSoup

from parsers.base import ParsedHolding, Parser


# 表頭欄位識別關鍵字
COL_STOCK_ID = ("股票代號", "代號", "代碼", "證券代號", "stock id", "stock code", "ticker")
COL_STOCK_NAME = ("股票名稱", "證券名稱", "名稱", "name")
COL_SHARES = ("持股數", "股數", "持有股數", "shares", "share")
COL_WEIGHT = ("比例", "權重", "佔基金比例", "weight", "%")

# AUM 識別
AUM_PATTERNS = (
    re.compile(r"(?:基金|資產)\s*規模[^0-9]{0,15}([0-9,]+)"),
    re.compile(r"net\s*asset\s*value[^0-9]{0,15}\$?\s*([0-9,]+)", re.IGNORECASE),
    re.compile(r"AUM[^0-9]{0,15}\$?\s*([0-9,]+)", re.IGNORECASE),
    re.compile(r"NT\$\s*([0-9,]+)\s*元?(?:\s*\(基金規模\))?"),
)


def _to_int(value: str) -> int | None:
    cleaned = re.sub(r"[,\s]", "", value)
    if not cleaned:
        return None
    try:
        return int(cleaned)
    except ValueError:
        try:
            return int(float(cleaned))
        except ValueError:
            return None


def _to_float(value: str) -> float | None:
    cleaned = value.replace("%", "").replace(",", "").strip()
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _match_col(header: str, keywords: tuple[str, ...]) -> bool:
    h = header.lower().strip()
    return any(k in h for k in keywords)


def _find_aum(soup: BeautifulSoup) -> int | None:
    text = soup.get_text(" ", strip=True)
    for pattern in AUM_PATTERNS:
        match = pattern.search(text)
        if match:
            return _to_int(match.group(1))
    return None


class GenericTableParser(Parser):
    def parse(self, html: str) -> ParsedHolding:
        soup = BeautifulSoup(html, "lxml")
        result = ParsedHolding()

        for table in soup.find_all("table"):
            holdings = self._parse_table(table)
            if holdings:
                result.holdings = holdings
                break  # 取第一張命中的表

        result.aum = _find_aum(soup)
        return result

    def parse_aum_only(self, html: str) -> int | None:
        soup = BeautifulSoup(html, "lxml")
        return _find_aum(soup)

    def _parse_table(self, table) -> list[dict]:
        rows = table.find_all("tr")
        if len(rows) < 2:
            return []

        # 找出表頭列（含至少一個 <th>，或第一列）
        header_cells: list[str] = []
        body_start = 0
        for idx, row in enumerate(rows):
            cells = row.find_all(["th", "td"])
            texts = [c.get_text(strip=True) for c in cells]
            if any(_match_col(t, COL_STOCK_ID) for t in texts) and any(
                _match_col(t, COL_SHARES) for t in texts
            ):
                header_cells = texts
                body_start = idx + 1
                break

        if not header_cells:
            return []

        col_idx: dict[str, int] = {}
        for i, h in enumerate(header_cells):
            if "stock_id" not in col_idx and _match_col(h, COL_STOCK_ID):
                col_idx["stock_id"] = i
            elif "stock_name" not in col_idx and _match_col(h, COL_STOCK_NAME):
                col_idx["stock_name"] = i
            elif "shares" not in col_idx and _match_col(h, COL_SHARES):
                col_idx["shares"] = i
            elif "weight" not in col_idx and _match_col(h, COL_WEIGHT):
                col_idx["weight"] = i

        if "stock_id" not in col_idx or "shares" not in col_idx:
            return []

        holdings: list[dict] = []
        for row in rows[body_start:]:
            cells = row.find_all(["td", "th"])
            if len(cells) <= max(col_idx.values()):
                continue
            stock_id = cells[col_idx["stock_id"]].get_text(strip=True)
            if not stock_id or not re.search(r"[0-9A-Z]{3,}", stock_id):
                continue
            stock_id = re.search(r"[0-9A-Z]{3,}", stock_id).group(0)
            shares = _to_int(cells[col_idx["shares"]].get_text(strip=True))
            if shares is None:
                continue
            holding = {
                "stock_id": stock_id,
                "stock_name": (
                    cells[col_idx["stock_name"]].get_text(strip=True)
                    if "stock_name" in col_idx
                    else None
                ),
                "shares_held": shares,
                "weight_pct": (
                    _to_float(cells[col_idx["weight"]].get_text(strip=True))
                    if "weight" in col_idx
                    else None
                ),
            }
            holdings.append(holding)
        return holdings
