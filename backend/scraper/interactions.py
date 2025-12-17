import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class InteractionHandler:
    """
    Handles user interactions on web pages during dynamic scraping.
    """

    def __init__(self, page):
        self.page = page
        self.interactions = {
            "clicks": [],
            "scrolls": 0,
            "pages": []
        }

    async def perform_click(self, selector: str) -> bool:
        """
        Perform a click on an element specified by selector.
        """
        try:
            await self.page.click(selector)
            self.interactions["clicks"].append({"selector": selector, "type": "click"})
            logger.info(f"Clicked on {selector}")
            return True
        except Exception as e:
            logger.error(f"Failed to click on {selector}: {e}")
            return False

    async def perform_scroll(self, direction: str = "down", pixels: int = 500) -> bool:
        """
        Perform a scroll action.
        """
        try:
            if direction == "down":
                await self.page.evaluate(f"window.scrollBy(0, {pixels});")
            elif direction == "up":
                await self.page.evaluate(f"window.scrollBy(0, -{pixels});")
            self.interactions["scrolls"] += 1
            logger.info(f"Scrolled {direction} by {pixels} pixels")
            return True
        except Exception as e:
            logger.error(f"Failed to scroll: {e}")
            return False

    async def wait_for_load(self, timeout: int = 5000):
        """
        Wait for the page to load.
        """
        try:
            await self.page.wait_for_load_state("networkidle", timeout=timeout)
        except Exception as e:
            logger.warning(f"Page load wait failed: {e}")

    def get_interactions(self) -> Dict[str, Any]:
        """
        Get the recorded interactions.
        """
        return self.interactions
