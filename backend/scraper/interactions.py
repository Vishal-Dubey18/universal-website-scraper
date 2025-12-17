# backend/scraper/interactions.py

from typing import List, Dict, Any
import logging
from backend.config import config

logger = logging.getLogger(__name__)


class InteractionHandler:
    """
    Centralized interaction tracker.
    Keeps record of clicks, scrolls, visited pages, and interaction-level errors.
    """

    def __init__(self, url: str):
        self.url = url
        self.interactions: Dict[str, Any] = {
            "clicks": [],
            "scrolls": 0,
            "pages": [url],
        }
        self.errors: List[Dict[str, str]] = []

    # ---------- Recording methods ----------

    def add_click(self, selector: str) -> None:
        """Record a click selector if valid"""
        if selector and isinstance(selector, str):
            self.interactions["clicks"].append(selector)

    def add_scroll(self, count: int = 1) -> None:
        """Increment scroll count"""
        if isinstance(count, int) and count > 0:
            self.interactions["scrolls"] += count

    def add_page(self, url: str) -> None:
        """Record a newly visited page"""
        if url and isinstance(url, str) and url not in self.interactions["pages"]:
            self.interactions["pages"].append(url)

    def add_error(self, message: str, phase: str) -> None:
        """Record interaction-related error"""
        if not message or not phase:
            return

        error = {
            "message": str(message),
            "phase": str(phase),
        }
        self.errors.append(error)
        logger.warning(f"Interaction error [{phase}]: {message}")

    # ---------- Retrieval methods ----------

    def get_interactions(self) -> Dict[str, Any]:
        """Return sanitized interaction data"""
        return {
            "clicks": list(self.interactions.get("clicks", [])),
            "scrolls": int(self.interactions.get("scrolls", 0)),
            "pages": list(self.interactions.get("pages", [])),
        }

    def get_errors(self) -> List[Dict[str, str]]:
        """Return recorded interaction errors"""
        return list(self.errors)

    # ---------- Control logic ----------

    def should_continue(self, current_depth: int) -> bool:
        """
        Decide whether interactions should continue
        based on configured max depth.
        """
        if not isinstance(current_depth, int):
            return False
        return current_depth < config.MAX_DEPTH
