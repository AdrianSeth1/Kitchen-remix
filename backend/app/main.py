"""
FastAPI application entry point.

Phase 0: serves /health and static frontend files.
Phase 1+: load_pipeline() is called in the lifespan handler so the model
is warm before any request arrives.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .routes import router
from . import pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Loading model pipeline…")
    pipeline.load_pipeline()
    logger.info("Pipeline ready (loaded=%s)", pipeline.is_loaded())
    yield
    logger.info("Shutting down.")


app = FastAPI(title="Kitchen Remix", version="0.1.0", lifespan=lifespan)
app.include_router(router, prefix="/api")

# Serve built frontend in production; skipped in dev (Vite runs separately).
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str):
        index = FRONTEND_DIST / "index.html"
        return FileResponse(index)
