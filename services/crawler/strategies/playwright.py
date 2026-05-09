from playwright.async_api import async_playwright

from strategies.base import CrawlerStrategy


class PlaywrightCrawler(CrawlerStrategy):
    """Layer 2：Playwright 無頭瀏覽器（規格 §6.1）。"""

    async def fetch(self, url: str) -> str:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle")
            content = await page.content()
            await browser.close()
            return content
