# backend/schemas.py
from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional
from datetime import datetime


class ErrorResponse(BaseModel):
    message: str
    phase: str


class MetaData(BaseModel):
    title: str = ""
    description: str = ""
    language: str = "en"
    canonical: Optional[HttpUrl] = None


class Link(BaseModel):
    text: str = ""
    href: HttpUrl


class Image(BaseModel):
    src: HttpUrl
    alt: str = ""


class SectionContent(BaseModel):
    headings: List[str] = Field(default_factory=list)
    text: str = ""
    links: List[Link] = Field(default_factory=list)
    images: List[Image] = Field(default_factory=list)
    lists: List[List[str]] = Field(default_factory=list)
    tables: List[List[List[str]]] = Field(default_factory=list)


class Section(BaseModel):
    id: str
    type: str
    label: str
    sourceUrl: HttpUrl
    content: SectionContent
    rawHtml: str
    truncated: bool = False


class Interactions(BaseModel):
    clicks: List[str] = Field(default_factory=list)
    scrolls: int = 0
    pages: List[str] = Field(default_factory=list)


class ScrapeResult(BaseModel):
    url: HttpUrl
    scrapedAt: str
    meta: MetaData
    sections: List[Section] = Field(default_factory=list)
    interactions: Interactions
    errors: List[ErrorResponse] = Field(default_factory=list)
    _strategy: Optional[str] = None


class ScrapeRequest(BaseModel):
    url: HttpUrl
    use_js: Optional[bool] = None
    max_depth: int = Field(default=3, ge=1, le=5)


class HealthResponse(BaseModel):
    status: str = "ok"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
