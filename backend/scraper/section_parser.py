# backend/scraper/section_parser.py

import logging
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup, Tag

from backend.config import config
from backend.scraper.utils import (
    make_absolute_url,
    sanitize_text,
    truncate_text,
)

logger = logging.getLogger(__name__)


class SectionParser:
    """
    Robust section parser:
    - Semantic sections first
    - Intelligent DIV fallback for content-heavy pages
    - Zero empty / duplicate sections

    """

    def __init__(self, html: str, base_url: str):
        self.base_url = base_url
        self.soup = BeautifulSoup(html, "lxml")

    # ==================================================
    # PUBLIC API
    # ==================================================
    def parse_sections(self) -> List[Dict[str, Any]]:
        sections: List[Dict[str, Any]] = []
        seen_hashes = set()

        semantic = self._find_semantic_sections()

        if len(semantic) < 2:
            semantic.extend(self._find_content_divs())

        for idx, data in enumerate(semantic):
            section = self._process_section(data, idx)
            if not section:
                continue

            # Skip tiny nav sections
            if section["type"] == "nav" and len(section["content"]["text"]) < 50:
                logger.debug(f"Skipping tiny nav section: {section['id']}")
                continue

            text = section["content"]["text"]
            if not text:
                continue

            sig = hash(text[:300])
            if sig in seen_hashes:
                logger.debug(f"Skipping duplicate section: {section['id']}")
                continue

            seen_hashes.add(sig)
            sections.append(section)

        if not sections:
            logger.warning("No sections found, using fallback")
            sections.append(self._create_fallback_section())

        logger.debug(f"Parsed {len(sections)} total sections")

        return sections

    # ==================================================
    # SECTION DISCOVERY
    # ==================================================
    def _find_semantic_sections(self) -> List[Dict[str, Any]]:
        tags = ["main", "section", "article", "nav", "aside", "footer", "header"]
        sections = []

        for tag in tags:
            for el in self.soup.find_all(tag):
                sections.append({
                    "element": el,
                    "html": str(el),
                })

        logger.debug(f"Found {len(sections)} semantic sections")

        return sections

    def _find_content_divs(self) -> List[Dict[str, Any]]:
        """
        Detect meaningful DIV containers (quotes.toscrape fix)
        """
        sections = []

        for div in self.soup.find_all("div"):
            text = sanitize_text(div.get_text(" ", strip=True))
            if len(text) < 300:
                continue

            # repeated child blocks heuristic
            child_divs = div.find_all("div", recursive=False)
            if len(child_divs) < 2:
                continue

            sections.append({
                "element": div,
                "html": str(div),
            })

        logger.debug(f"Found {len(sections)} content DIVs as fallback")

        return sections

    # ==================================================
    # PROCESS SECTION
    # ==================================================
    def _process_section(
        self,
        data: Dict[str, Any],
        index: int,
    ) -> Optional[Dict[str, Any]]:
        el: Tag = data.get("element")
        if not el:
            return None

        content = self._extract_content(el)
        if not content["text"]:
            return None

        raw_html, truncated = truncate_text(
            data.get("html", ""),
            config.MAX_RAW_HTML_LENGTH,
        )

        return {
            "id": f"{el.name}-{index}",
            "type": el.name,
            "label": self._generate_label(el, content),
            "sourceUrl": self.base_url,
            "content": content,
            "rawHtml": raw_html,
            "truncated": truncated,
        }

    # ==================================================
    # CONTENT EXTRACTION
    # ==================================================
    def _extract_content(self, el: Tag) -> Dict[str, Any]:
        content = {
            "headings": [],
            "text": "",
            "links": [],
            "images": [],
            "lists": [],
            "tables": [],
        }

        # Headings
        for h in el.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            txt = h.get_text(strip=True)
            if txt:
                content["headings"].append(txt)

        # Text
        content["text"] = sanitize_text(
            el.get_text(" ", strip=True)
        )

        # Links
        for a in el.find_all("a", href=True):
            href = a["href"]
            if href.startswith(("#", "javascript:", "mailto:")):
                continue

            txt, _ = truncate_text(
                a.get_text(strip=True),
                config.MAX_LINK_TEXT_LENGTH,
            )

            content["links"].append({
                "text": txt,
                "href": make_absolute_url(href, self.base_url),
            })

        # Images
        for img in el.find_all("img", src=True):
            src = img["src"]

            # CRITICAL: Skip data: URLs (base64 encoded images) to prevent Pydantic validation errors
            if src.startswith("data:"):
                logger.debug(f"Skipping data: URL image")
                continue

            alt, _ = truncate_text(
                img.get("alt", ""),
                config.MAX_ALT_TEXT_LENGTH,
            )

            try:
                abs_url = make_absolute_url(src, self.base_url)
                content["images"].append({
                    "src": abs_url,
                    "alt": alt,
                })
            except Exception as e:
                logger.debug(f"Skipping invalid image URL: {src} - {e}")
                continue

        # Lists
        for ul in el.find_all(["ul", "ol"]):
            items = [
                li.get_text(strip=True)
                for li in ul.find_all("li")
                if li.get_text(strip=True)
            ]
            if items:
                content["lists"].append(items)

        # Tables
        for table in el.find_all("table"):
            rows = []
            for tr in table.find_all("tr"):
                row = [
                    td.get_text(strip=True)
                    for td in tr.find_all(["td", "th"])
                    if td.get_text(strip=True)
                ]
                if row:
                    rows.append(row)
            if rows:
                content["tables"].append(rows)

        return content

    # ==================================================
    # FALLBACK
    # ==================================================
    def _create_fallback_section(self) -> Dict[str, Any]:
        body = self.soup.body

        text = sanitize_text(
            body.get_text(" ", strip=True)
        ) if body else ""

        raw_html, truncated = truncate_text(
            str(body) if body else "",
            config.MAX_RAW_HTML_LENGTH,
        )

        return {
            "id": "main-0",
            "type": "section",
            "label": "Main Content",
            "sourceUrl": self.base_url,
            "content": {
                "headings": [],
                "text": text,
                "links": [],
                "images": [],
                "lists": [],
                "tables": [],
            },
            "rawHtml": raw_html,
            "truncated": truncated,
        }

    # ==================================================
    # LABEL
    # ==================================================
    def _generate_label(self, el: Tag, content: Dict[str, Any]) -> str:
        if content["headings"]:
            return content["headings"][0][:100]

        if el.get("aria-label"):
            return el["aria-label"][:100]

        return el.name.upper()
