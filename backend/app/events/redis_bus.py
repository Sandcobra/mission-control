from __future__ import annotations

import json
import logging

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = await aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_keepalive=True,
        )
    return _redis


async def publish_event(channel: str, event: dict) -> None:
    """Publish an event dict to a Redis pub/sub channel."""
    try:
        r = await get_redis()
        await r.publish(channel, json.dumps(event, default=str))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to publish event to channel %s: %s", channel, exc)


async def publish_agent_event(agent_id: str, event: dict) -> None:
    """Publish an agent-scoped event to both the per-agent and global channels."""
    await publish_event(f"agent:{agent_id}", event)
    await publish_event("agent_updates", event)


async def publish_task_event(task_id: str, event: dict) -> None:
    """Publish a task-scoped event to both the per-task and global channels."""
    await publish_event(f"task:{task_id}", event)
    await publish_event("task_updates", event)
