from pydantic_settings import BaseSettings
from typing import List
from enum import Enum


class ScrapingStrategy(str, Enum):
    AUTO = "auto"
    STATIC_ONLY = "static_only"
    JS_ONLY = "js_only"


class ScraperConfig(BaseSettings):
    APP_NAME: str = "Universal Website Scraper"
    APP_VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    STATIC_TIMEOUT: int = 30
    PLAYWRIGHT_TIMEOUT: int = 60
    INTERACTION_TIMEOUT: int = 10
    GLOBAL_TIMEOUT: int = 120

    JS_FALLBACK_MIN_TEXT: int = 400

    MAX_DEPTH: int = 3
    SCROLL_DELAY: float = 2.0
    SCROLL_ATTEMPTS: int = 3

    SECTION_TYPES: List[str] = [
        "hero", "section", "nav", "footer",
        "list", "grid", "faq", "pricing", "unknown"
    ]

    MAX_RAW_HTML_LENGTH: int = 10000
    MAX_LINK_TEXT_LENGTH: int = 200
    MAX_ALT_TEXT_LENGTH: int = 200

    NOISE_SELECTORS: List[str] = [
        '[class*="cookie"]',
        '[id*="cookie"]',
        '.modal',
        '.popup',
        '[class*="popup"]',
        '[class*="newsletter"]',
        '[class*="overlay"]',
        '[class*="ad"]',
        '[class*="banner"]',
        '[class*="ads"]',
        'script',
        'style',
        'iframe'
    ]

    USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    ALLOWED_SCHEMES: List[str] = ["http", "https"]
    LOG_LEVEL: str = "INFO"
    ENABLE_PLAYWRIGHT_HEADLESS: bool = True

    class Config:
        env_file = ".env"


config = ScraperConfig()
