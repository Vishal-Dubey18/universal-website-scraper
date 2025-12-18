import logging
from datetime import datetime
from typing import Dict, Any, Optional

from backend.config import config
from backend.scraper.static_scraper import StaticScraper
from backend.scraper.dynamic_scraper import DynamicScraper
from backend.scraper.section_parser import SectionParser
from backend.scraper.utils import is_valid_url, clean_url
import asyncio

logger = logging.getLogger(__name__)


class ScraperEngine:
    def __init__(self, url: str, use_js: Optional[bool], max_depth: int):
        self.url = clean_url(url)
        self.use_js = use_js

        self.result = {
            "url": self.url,
            "scrapedAt": datetime.utcnow().isoformat() + "Z",
            "meta": {},
            "sections": [],
            "interactions": {"clicks": [], "scrolls": 0, "pages": [self.url]},
            "errors": [],
        }

    async def scrape(self) -> Dict[str, Any]:
        try:
            return await asyncio.wait_for(self._scrape_internal(), timeout=config.GLOBAL_TIMEOUT)
        except asyncio.TimeoutError:
            self._error("Scraping exceeded global timeout", "timeout")
            return self.result

    async def _scrape_internal(self) -> Dict[str, Any]:
        if not is_valid_url(self.url):
            self._error("Invalid URL", "validation")
            return self.result

        static_ok = await self._static()

        if self.use_js or (static_ok and self._low_text()):
            logger.info("Triggering JS rendering (user request or low content detected)")
            await self._dynamic()

        return self.result

    async def _static(self) -> bool:
        scraper = StaticScraper(self.url)
        if not await scraper.fetch():
            return False

        self.result["meta"] = scraper.extract_metadata()
        html = scraper.get_html()

        if html:
            self.result["sections"] = SectionParser(html, self.url).parse_sections()

        return True

    async def _dynamic(self):
        scraper = DynamicScraper(self.url)
        try:
            if await scraper.fetch():
                html = scraper.get_html()
                if html:
                    self.result["sections"] = SectionParser(html, self.url).parse_sections()
                self.result["interactions"] = await scraper.perform_interactions()
        finally:
            # Guaranteed cleanup of browser resources
            await scraper.close()

    def _low_text(self):
        total = sum(len(s["content"]["text"]) for s in self.result["sections"])
        return total < config.JS_FALLBACK_MIN_TEXT

    def _error(self, msg, phase):
        self.result["errors"].append({"message": msg, "phase": phase})
