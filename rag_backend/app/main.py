"""
main.py
--------
FastAPI application entrypoint.

Wires together:
  - Static files & Jinja2 templates
  - Routers (auth, documents, chat, ui)
  - Custom exception-logging middleware
  - Startup/shutdown events (MongoDB connection, index creation, model preload)
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import close_mongo_connection, connect_to_mongo, ensure_indexes
from app.middleware.exception_handler import ExceptionLoggingMiddleware
from app.routes import auth, chat, document, ui
from app.utils.embeddings import preload_model

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---- Startup ----
    logger.info("Starting up %s (env=%s)...", settings.APP_NAME, settings.APP_ENV)
    await connect_to_mongo()
    await ensure_indexes()
    preload_model()  # Load the SentenceTransformer model exactly once.
    logger.info("Startup complete.")

    yield

    # ---- Shutdown ----
    logger.info("Shutting down...")
    await close_mongo_connection()
    logger.info("Shutdown complete.")


app = FastAPI(
    title=settings.APP_NAME,
    description="FastAPI + AI Retrieval Augmented Generation backend.",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
app.add_middleware(ExceptionLoggingMiddleware)

# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(ui.router)
app.include_router(auth.router)
app.include_router(document.router)
app.include_router(chat.router)


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Simple liveness probe used by Docker/Compose healthchecks."""
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}
