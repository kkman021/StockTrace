from abc import ABC, abstractmethod


class CrawlerStrategy(ABC):
    @abstractmethod
    async def fetch(self, url: str) -> str: ...
