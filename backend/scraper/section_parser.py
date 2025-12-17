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
    Parse cleaned HTML into structured sections using BeautifulSoup + lxml.
    Handles:
    - Semantic sections
    - Deduplication
    - Robust fallback for JS-heavy pages
    """

    def __init__(self, html: str, base_url: str):
        self.base_url = base_url
        self.soup = BeautifulSoup(html, "lxml")

    # ==========================================================
    # PUBLIC API
    # ==========================================================
    def parse_sections(self) -> List[Dict[str, Any]]:
        sections: List[Dict[str, Any]] = []
        seen_hashes = set()

        semantic_sections = self._find_semantic_sections()

        for index, section_data in enumerate(semantic_sections):
            section = self._process_section(section_data, index)
            if not section:
                continue

            text = section["content"]["text"]
            if not text:
                continue

            text_hash = hash(text[:300])
            if text_hash in seen_hashes:
                continue

            seen_hashes.add(text_hash)
            sections.append(section)

        if not sections:
            sections.append(self._create_fallback_section())

        return sections

    # ==========================================================
    # SECTION DISCOVERY
    # ==========================================================
    def _find_semantic_sections(self) -> List[Dict[str, Any]]:
        sections = []
        semantic_tags = [
            "main",
            "section",
            "article",
            "nav",
            "aside",
            "footer",
            "header",
        ]

        for tag in semantic_tags:
            for el in self.soup.find_all(tag):
                sections.append({
                    "element": el,
                    "html": str(el),
                })

        return sections

    # ==========================================================
    # SECTION PROCESSING
    # ==========================================================
    def _process_section(
        self,
        section_data: Dict[str, Any],
        index: int
    ) -> Optional[Dict[str, Any]]:
        element: Tag = section_data.get("element")
        if not element:
            return None

        content = self._extract_content(element)
        if not content["text"]:
            return None

        raw_html, truncated = truncate_text(
            section_data.get("html", ""),
            config.MAX_RAW_HTML_LENGTH,
        )

        return {
            "id": f"{element.name}-{index}",
            "type": element.name,
            "label": self._generate_label(element, content),
            "sourceUrl": self.base_url,
            "content": content,
            "rawHtml": raw_html,
            "truncated": truncated,
        }

    # ==========================================================
    # CONTENT EXTRACTION
    # ==========================================================
    def _extract_content(self, element: Tag) -> Dict[str, Any]:
        content = {
            "headings": [],
            "text": "",
            "links": [],
            "images": [],
            "lists": [],
            "tables": [],
        }

        # Headings
        for h in element.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            text = h.get_text(strip=True)
            if text:
                content["headings"].append(text)

        # Text
        content["text"] = sanitize_text(
            element.get_text(" ", strip=True)
        )

        # Links
        for a in element.find_all("a", href=True):
            href = a["href"]
            if href.startswith(("#", "javascript:", "mailto:")):
                continue

            link_text, _ = truncate_text(
                a.get_text(strip=True) or "",
                config.MAX_LINK_TEXT_LENGTH,
            )

            content["links"].append({
                "text": link_text,
                "href": make_absolute_url(href, self.base_url),
            })

        # Images
        for img in element.find_all("img", src=True):
            alt, _ = truncate_text(
                img.get("alt", ""),
                config.MAX_ALT_TEXT_LENGTH,
            )

            content["images"].append({
                "src": make_absolute_url(img["src"], self.base_url),
                "alt": alt,
            })

        # Lists
        for ul in element.find_all(["ul", "ol"]):
            items = [
                li.get_text(strip=True)
                for li in ul.find_all("li")
                if li.get_text(strip=True)
            ]
            if items:
                content["lists"].append(items)

        # Tables
        for table in element.find_all("table"):
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

    # ==========================================================
    # FALLBACK SECTION (CRITICAL FIX)
    # ==========================================================
    def _create_fallback_section(self) -> Dict[str, Any]:
        body = self.soup.body

        content = {
            "headings": [],
            "text": "",
            "links": [],
            "images": [],
            "lists": [],
            "tables": [],
        }

        if body:
            content["text"] = sanitize_text(
                body.get_text(" ", strip=True)
            )

            for a in body.find_all("a", href=True):
                href = a["href"]
                if href.startswith(("#", "javascript:", "mailto:")):
                    continue

                content["links"].append({
                    "text": a.get_text(strip=True),
                    "href": make_absolute_url(href, self.base_url),
                })

            for img in body.find_all("img", src=True):
                content["images"].append({
                    "src": make_absolute_url(img["src"], self.base_url),
                    "alt": img.get("alt", ""),
                })

        raw_html, truncated = truncate_text(
            str(body) if body else "",
            config.MAX_RAW_HTML_LENGTH,
        )

        return {
            "id": "main-0",
            "type": "section",
            "label": "Main Content",
            "sourceUrl": self.base_url,
            "content": content,
            "rawHtml": raw_html,
            "truncated": truncated,
        }

    # ==========================================================
    # LABEL GENERATION
    # ==========================================================
    def _generate_label(
        self,
        element: Tag,
        content: Dict[str, Any],
    ) -> str:
        if content["headings"]:
            return content["headings"][0][:100]

        if element.get("aria-label"):
            return element["aria-label"][:100]

        return element.name.upper()
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
                continue

            text = section["content"]["text"]
            if not text:
                continue

            sig = hash(text[:300])
            if sig in seen_hashes:
                continue

            seen_hashes.add(sig)
            sections.append(section)

        if not sections:
            sections.append(self._create_fallback_section())

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
            alt, _ = truncate_text(
                img.get("alt", ""),
                config.MAX_ALT_TEXT_LENGTH,
            )
            content["images"].append({
                "src": make_absolute_url(img["src"], self.base_url),
                "alt": alt,
            })

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
