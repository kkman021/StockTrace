"""Tests for GenericTableParser."""
from parsers.generic_table import GenericTableParser


def _load(name: str) -> str:
    with open(f"tests/fixtures/{name}") as f:
        return f.read()


class TestGenericTableParser:
    def test_parses_canonical_disclosure(self):
        parser = GenericTableParser()
        result = parser.parse(_load("sample_disclosure.html"))

        # Should pick up 5 valid rows (skipping the colspan-合計 row)
        assert len(result.holdings) == 5
        first = result.holdings[0]
        assert first["stock_id"] == "2330"
        assert first["stock_name"] == "台積電"
        assert first["shares_held"] == 1_234_567
        assert first["weight_pct"] == 15.23

    def test_aum_extracted_from_inline_text(self):
        parser = GenericTableParser()
        result = parser.parse(_load("sample_disclosure.html"))
        assert result.aum == 1_234_567_890

    def test_skips_summary_row_without_valid_stock_id(self):
        parser = GenericTableParser()
        result = parser.parse(_load("sample_disclosure.html"))
        ids = [h["stock_id"] for h in result.holdings]
        # 合計 row 不應出現
        assert all(id_.isalnum() for id_ in ids)
        assert len(ids) == 5

    def test_handles_empty_html(self):
        parser = GenericTableParser()
        result = parser.parse("<html><body>no table</body></html>")
        assert result.holdings == []
        assert result.aum is None

    def test_handles_malformed_table_without_required_cols(self):
        html = """
        <html><body><table>
          <tr><th>Foo</th><th>Bar</th></tr>
          <tr><td>1</td><td>2</td></tr>
        </table></body></html>
        """
        result = GenericTableParser().parse(html)
        assert result.holdings == []

    def test_aum_alternate_format(self):
        html = """
        <html><body>
          <p>Net Asset Value: $9,876,543,210</p>
          <table>
            <tr><th>股票代號</th><th>股數</th></tr>
            <tr><td>2330</td><td>100,000</td></tr>
          </table>
        </body></html>
        """
        parser = GenericTableParser()
        result = parser.parse(html)
        assert result.aum == 9_876_543_210
        assert len(result.holdings) == 1
