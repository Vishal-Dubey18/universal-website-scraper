import sys
import asyncio

# -------------------------------------------------
# Windows + Playwright Fix (REQUIRED)
# -------------------------------------------------
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import logging
from datetime import datetime

from backend.schemas import ScrapeRequest, ScrapeResult, HealthResponse
from backend.scraper.engine import ScraperEngine
from backend.config import config

logging.basicConfig(
    level=config.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=config.APP_NAME,
    description="Universal Website Scraper MVP",
    version=config.APP_VERSION,
)

templates = Jinja2Templates(directory="backend/templates")
app.mount("/static", StaticFiles(directory="backend/static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/healthz", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow().isoformat() + "Z",
    )


@app.post("/scrape", response_model=ScrapeResult)
async def scrape_url(request: ScrapeRequest):
    logger.info(f"Scrape request received for URL: {request.url}")

    try:
        scraper = ScraperEngine(
            url=str(request.url),
            use_js=request.use_js,
            max_depth=request.max_depth,
        )

        result = await scraper.scrape()
        return ScrapeResult(**result)

    except Exception as e:
        logger.exception("Scraping failed")
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "phase": "scrape_engine",
                "url": str(request.url),
            },
        )


@app.get("/api/docs")
async def api_docs():
    return {
        "endpoints": {
            "GET /": "Frontend UI",
            "GET /healthz": "Health check",
            "POST /scrape": "Scrape a URL",
        },
        "version": config.APP_VERSION,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
    )
