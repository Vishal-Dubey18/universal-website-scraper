# backend/scraper/utils.py

import re
from typing import Optional, Tuple
from urllib.parse import urlparse, urljoin
from backend.config import config


def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        if not result.scheme or not result.netloc:
            return False
        return result.scheme in config.ALLOWED_SCHEMES
    except Exception:
        return False


def clean_url(url: str) -> str:
    if not url:
        return url

    url = url.strip()

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    return url.rstrip("/")


def make_absolute_url(url: str, base_url: str) -> str:
    if not url:
        return url

    if url.startswith("//"):
        return "https:" + url

    if url.startswith(("http://", "https://")):
        return url

    return urljoin(base_url, url)


def truncate_text(text: str, max_length: int) -> Tuple[str, bool]:
    if not text or len(text) <= max_length:
        return text, False

    return text[:max_length] + "...", True


def extract_domain(url: str) -> Optional[str]:
    try:
        return urlparse(url).netloc
    except Exception:
        return None


def is_same_domain(url1: str, url2: str) -> bool:
    d1 = extract_domain(url1)
    d2 = extract_domain(url2)

    if not d1 or not d2:
        return False

    return d1.replace("www.", "") == d2.replace("www.", "")


def sanitize_text(text: str) -> str:
    if not text:
        return ""

    return re.sub(r"\s+", " ", text).strip()
