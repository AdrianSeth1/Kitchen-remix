"""
FastAPI application entry point.

Model loads once in the lifespan hook so it is warm before the first request.
Inference always runs in a threadpool — the event loop is never blocked.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Load .env before config imports so HF_TOKEN is available.
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from .routes import router
from . import pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Loading model pipeline …")
    pipeline.load_pipeline()
    logger.info("Pipeline ready (loaded=%s)", pipeline.is_loaded())
    yield
    logger.info("Shutting down.")


app = FastAPI(title="Kitchen Remix", version="0.1.0", lifespan=lifespan)
app.include_router(router, prefix="/api")

# Serve built frontend in production; skipped in dev (Vite dev server runs separately).
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str):
        return FileResponse(FRONTEND_DIST / "index.html")
