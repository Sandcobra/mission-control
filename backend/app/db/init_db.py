from __future__ import annotations

import logging

from app.db.base import Base, engine
from app.db import models  # noqa: F401 – ensure all models are registered

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """Create all database tables if they do not exist."""
    logger.info("Initialising database schema …")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema ready.")
