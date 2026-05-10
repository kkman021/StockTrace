from strategies.base import CrawlerStrategy


class PlaywrightCrawler(CrawlerStrategy):
    """Layer 2：Playwright 無頭瀏覽器（規格 §6.1）。

    playwright 透過 Microsoft 官方 base image 在 production 內安裝；
    匯入採延遲式以利 light-only 環境（含部分測試）也能載入此模組。
    """

    async def fetch(self, url: str) -> str:
        from playwright.async_api import async_playwright  # 延遲匯入

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle")
            content = await page.content()
            await browser.close()
            return content
