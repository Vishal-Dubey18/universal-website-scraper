import httpx
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any
import logging

from backend.config import config
from backend.scraper.utils import make_absolute_url

logger = logging.getLogger(__name__)


class StaticScraper:
    def __init__(self, url: str):
        self.url = url
        self.soup: Optional[BeautifulSoup] = None

    async def fetch(self) -> bool:
        try:
            async with httpx.AsyncClient(
                timeout=config.STATIC_TIMEOUT,
                follow_redirects=True,
                headers={"User-Agent": config.USER_AGENT},
            ) as client:
                res = await client.get(self.url)
                res.raise_for_status()
                self.soup = BeautifulSoup(res.text, "lxml")
                return True
        except Exception as e:
            logger.error(f"Static fetch failed: {e}")
            return False

    def extract_metadata(self) -> Dict[str, Any]:
        if not self.soup:
            return {}

        return {
            "title": self.soup.title.string.strip() if self.soup.title else "",
            "description": "",
            "language": self.soup.html.get("lang", "en") if self.soup.html else "en",
            "canonical": None,
        }

    def get_html(self) -> Optional[str]:
        return str(self.soup) if self.soup else None
