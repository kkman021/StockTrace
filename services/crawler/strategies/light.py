import httpx

from strategies.base import CrawlerStrategy


class LightCrawler(CrawlerStrategy):
    """Layer 1：httpx 輕量爬取（規格 §6.1）。"""

    async def fetch(self, url: str) -> str:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text
