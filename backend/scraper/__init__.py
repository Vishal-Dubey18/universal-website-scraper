# backend/scraper/__init__.py

from backend.scraper.engine import ScraperEngine
from backend.scraper.static_scraper import StaticScraper
from backend.scraper.dynamic_scraper import DynamicScraper
from backend.scraper.section_parser import SectionParser
from backend.scraper.interactions import InteractionHandler

__all__ = [
    "ScraperEngine",
    "StaticScraper",
    "DynamicScraper",
    "SectionParser",
    "InteractionHandler",
]
