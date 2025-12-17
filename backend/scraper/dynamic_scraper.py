# backend/scraper/dynamic_scraper.py

from playwright.async_api import async_playwright, Page, BrowserContext, Playwright
from typing import List, Optional, Dict, Any
import logging
from backend.config import config
from backend.scraper.utils import make_absolute_url

logger = logging.getLogger(__name__)


class DynamicScraper:
    def __init__(self, url: str):
        self.url = url
        self.html: Optional[str] = None

        self.playwright: Optional[Playwright] = None
        self.browser = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        self.visited_pages: List[str] = [url]

    async def fetch(self) -> bool:
        """Start Playwright, open page, render HTML"""
        try:
            logger.info(f"Launching Playwright for {self.url}")

            self.playwright = await async_playwright().start()

            self.browser = await self.playwright.chromium.launch(
                headless=config.ENABLE_PLAYWRIGHT_HEADLESS,
                args=["--no-sandbox", "--disable-setuid-sandbox"],
            )

            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=config.USER_AGENT,
                java_script_enabled=True,
            )

            self.page = await self.context.new_page()
            self.page.set_default_timeout(config.PLAYWRIGHT_TIMEOUT * 1000)

            logger.info(f"Navigating to {self.url}")
            await self.page.goto(
                self.url,
                wait_until="networkidle",
                timeout=config.PLAYWRIGHT_TIMEOUT * 1000,
            )

            await self._wait_for_content()
            await self._remove_noise()

            self.html = await self.page.content()
            logger.info("Dynamic fetch successful")
            return True

        except Exception as e:
            logger.error(f"Playwright fetch failed: {e}")
            return False

    async def _wait_for_content(self):
        if not self.page:
            return

        await self.page.wait_for_timeout(2000)

        selectors = ["main", "article", "[role='main']", "body"]
        for selector in selectors:
            try:
                await self.page.wait_for_selector(selector, timeout=5000)
                return
            except Exception:
                continue

    async def _remove_noise(self):
        if not self.page:
            return

        for selector in config.NOISE_SELECTORS:
            try:
                await self.page.evaluate(
                    """
                    (sel) => {
                        document.querySelectorAll(sel).forEach(el => el.remove());
                    }
                    """,
                    selector,
                )
            except Exception:
                pass

    async def perform_interactions(self) -> Dict[str, Any]:
        if not self.page:
            return {"clicks": [], "scrolls": 0, "pages": self.visited_pages}

        clicks: List[str] = []

        clicks.extend(await self._click_tabs())
        clicks.extend(await self._click_load_buttons())

        scrolls = await self._scroll_for_content()
        await self._handle_pagination()

        return {
            "clicks": clicks,
            "scrolls": scrolls,
            "pages": self.visited_pages,
        }

    async def _click_tabs(self) -> List[str]:
        if not self.page:
            return []

        clicked: List[str] = []
        selectors = ["[role='tab']", ".tab", "[class*='tab']", "button[data-tab]"]

        for selector in selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                for el in elements[:3]:
                    if await el.is_visible():
                        try:
                            await el.click(timeout=config.INTERACTION_TIMEOUT * 1000)
                            clicked.append(selector)
                            await self.page.wait_for_timeout(1000)
                        except Exception:
                            pass
            except Exception:
                pass

        return clicked

    async def _click_load_buttons(self) -> List[str]:
        if not self.page:
            return []

        clicked: List[str] = []
        selectors = [
            'button:has-text("Load")',
            'button:has-text("More")',
            'button:has-text("Show")',
            'a:has-text("Load more")',
            'a:has-text("Show more")',
        ]

        for selector in selectors:
            try:
                buttons = await self.page.query_selector_all(selector)
                for btn in buttons[:2]:
                    if await btn.is_visible():
                        try:
                            await btn.click(timeout=config.INTERACTION_TIMEOUT * 1000)
                            clicked.append(selector)
                            await self.page.wait_for_timeout(2000)
                        except Exception:
                            pass
            except Exception:
                pass

        return clicked

    async def _scroll_for_content(self) -> int:
        if not self.page:
            return 0

        scrolls = 0

        for _ in range(config.SCROLL_ATTEMPTS):
            try:
                old_height = await self.page.evaluate("document.body.scrollHeight")
                await self.page.evaluate(
                    "window.scrollTo(0, document.body.scrollHeight)"
                )
                await self.page.wait_for_timeout(int(config.SCROLL_DELAY * 1000))
                new_height = await self.page.evaluate("document.body.scrollHeight")

                scrolls += 1
                if new_height == old_height:
                    break
            except Exception:
                break

        return scrolls

    async def _handle_pagination(self):
        if not self.page:
            return

        selectors = [
            'a:has-text("Next")',
            ".next",
            "[rel='next']",
            'button:has-text("Next")',
            'a:has-text("»")',
        ]

        for _ in range(config.MAX_DEPTH - 1):
            found = False

            for selector in selectors:
                try:
                    link = await self.page.query_selector(selector)
                    if link and await link.is_visible():
                        href = await link.get_attribute("href")
                        if not href:
                            continue

                        await link.click(timeout=config.INTERACTION_TIMEOUT * 1000)
                        await self.page.wait_for_load_state("networkidle")

                        current = self.page.url
                        if current not in self.visited_pages:
                            self.visited_pages.append(current)

                        found = True
                        break
                except Exception:
                    continue

            if not found:
                break

    def get_html(self) -> Optional[str]:
        return self.html

    async def close(self):
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.warning(f"Playwright cleanup failed: {e}")
