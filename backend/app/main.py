from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import agents, metrics, runs, tasks
from app.api.websocket import DEFAULT_RELAY_CHANNELS, router as ws_router
from app.config import settings
from app.db.init_db import init_db
from app.events.websocket_manager import redis_to_websocket_relay

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s – %(message)s",
)
logger = logging.getLogger(__name__)

_relay_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global _relay_task

    # --- Startup ---
    logger.info("Starting Mission Control API …")

    # Initialise database schema
    try:
        await init_db()
    except Exception as exc:
        logger.error("Database initialisation failed: %s", exc)
        # Allow the app to start even if the DB isn't available yet; routes
        # will surface errors when accessed.

    # Start Redis → WebSocket relay as a background task
    try:
        _relay_task = asyncio.create_task(
            redis_to_websocket_relay(DEFAULT_RELAY_CHANNELS),
            name="redis_ws_relay",
        )
        logger.info("Redis WebSocket relay started.")
    except Exception as exc:
        logger.warning("Could not start Redis relay: %s", exc)

    yield

    # --- Shutdown ---
    logger.info("Shutting down Mission Control API …")
    if _relay_task and not _relay_task.done():
        _relay_task.cancel()
        try:
            await _relay_task
        except asyncio.CancelledError:
            pass


def create_app() -> FastAPI:
    app = FastAPI(
        title="Mission Control",
        version="1.0.0",
        description=(
            "Central command-and-control API for autonomous AI agent fleets. "
            "Handles agent registration, heartbeats, task orchestration, "
            "real-time event streaming, cost tracking, and observability metrics."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ---------------------------------------------------------------------------
    # CORS – allow all origins in development; tighten in production
    # ---------------------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---------------------------------------------------------------------------
    # Routers
    # ---------------------------------------------------------------------------
    app.include_router(agents.router)
    app.include_router(tasks.router)
    app.include_router(runs.router)
    app.include_router(metrics.router)
    app.include_router(ws_router)

    # ---------------------------------------------------------------------------
    # Health check
    # ---------------------------------------------------------------------------
    @app.get("/health", tags=["health"], summary="Health check")
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
