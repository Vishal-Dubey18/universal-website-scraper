import httpx
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any
import logging

from backend.config import config
from backend.scraper.utils import make_absolute_url

logger = logging.getLogger(__name__)

try:
    from selectolax.parser import HTMLParser
except Exception:
    HTMLParser = None


class StaticScraper:
    def __init__(self, url: str):
        self.url = url
        self.soup: Optional[BeautifulSoup] = None
        self.tree = None

    async def fetch(self) -> bool:
        try:
            async with httpx.AsyncClient(
                timeout=config.STATIC_TIMEOUT,
                follow_redirects=True,
                headers={"User-Agent": config.USER_AGENT},
            ) as client:
                res = await client.get(self.url)
                res.raise_for_status()
                html = res.text

                # Prefer selectolax for fast parse if available
                if HTMLParser:
                    try:
                        self.tree = HTMLParser(html)
                    except Exception:
                        self.tree = None

                # Keep BeautifulSoup for downstream section parsing compatibility
                self.soup = BeautifulSoup(html, "lxml")
                return True
        except Exception as e:
            logger.error(f"Static fetch failed: {e}")
            return False

    def extract_metadata(self) -> Dict[str, Any]:
        # Attempt to use selectolax tree for metadata extraction when available
        title = ""
        description = ""
        canonical = None
        language = "en"

        if self.tree:
            try:
                t = self.tree.css_first("title")
                if t:
                    title = t.text()

                md = self.tree.css_first('meta[name="description"]')
                if md and md.attributes.get("content"):
                    description = md.attributes.get("content")

                lc = self.tree.css_first('link[rel="canonical"]')
                if lc and lc.attributes.get("href"):
                    canonical = lc.attributes.get("href")

                html_tag = self.tree.css_first("html")
                if html_tag and html_tag.attributes.get("lang"):
                    language = html_tag.attributes.get("lang")
            except Exception:
                # Fallback to BeautifulSoup
                self.tree = None

        if not self.tree and self.soup:
            if self.soup.title and self.soup.title.string:
                title = self.soup.title.string.strip()

            meta_desc = self.soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.get("content"):
                description = meta_desc.get("content", "")

            link_canonical = self.soup.find("link", attrs={"rel": "canonical"})
            if link_canonical and link_canonical.get("href"):
                canonical = link_canonical.get("href")

            if self.soup.html:
                language = self.soup.html.get("lang", "en")

        return {
            "title": title,
            "description": description,
            "language": language,
            "canonical": canonical,
        }

    def get_html(self) -> Optional[str]:
        return str(self.soup) if self.soup else None
