from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict
from typing import Any

from fastapi import WebSocket
from starlette.websockets import WebSocketState

from app.events.redis_bus import get_redis

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages active WebSocket connections grouped by channel name.

    Channels are arbitrary strings (e.g. "agent_updates", "task:uuid-…").
    Clients can subscribe to any channel; the manager fans out messages to all
    subscribers of that channel.
    """

    def __init__(self) -> None:
        # channel -> list of WebSocket connections
        self.active_connections: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, channel: str) -> None:
        await websocket.accept()
        self.active_connections[channel].append(websocket)
        logger.debug("WebSocket connected on channel '%s'", channel)

    def disconnect(self, websocket: WebSocket, channel: str) -> None:
        connections = self.active_connections.get(channel, [])
        if websocket in connections:
            connections.remove(websocket)
        logger.debug("WebSocket disconnected from channel '%s'", channel)

    async def broadcast(self, channel: str, message: dict[str, Any]) -> None:
        """Send a JSON message to all connections subscribed to `channel`."""
        dead: list[WebSocket] = []
        for ws in list(self.active_connections.get(channel, [])):
            try:
                if ws.client_state == WebSocketState.CONNECTED:
                    await ws.send_json(message)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to send to websocket on channel %s: %s", channel, exc)
                dead.append(ws)

        for ws in dead:
            self.disconnect(ws, channel)

    async def broadcast_all(self, message: dict[str, Any]) -> None:
        """Send a JSON message to every connected WebSocket across all channels."""
        for channel in list(self.active_connections.keys()):
            await self.broadcast(channel, message)


# Module-level singleton
manager = ConnectionManager()


async def redis_to_websocket_relay(channels: list[str]) -> None:
    """
    Long-running background task that subscribes to one or more Redis pub/sub
    channels and forwards received messages to the relevant WebSocket
    connections via the ConnectionManager singleton.

    This coroutine is designed to be started with asyncio.create_task() and
    run for the lifetime of the application.
    """
    while True:
        try:
            r = await get_redis()
            pubsub = r.pubsub()
            await pubsub.subscribe(*channels)
            logger.info("Redis relay subscribed to channels: %s", channels)

            async for raw_message in pubsub.listen():
                if raw_message["type"] != "message":
                    continue

                channel: str = raw_message["channel"]
                try:
                    payload: dict[str, Any] = json.loads(raw_message["data"])
                except (json.JSONDecodeError, TypeError):
                    payload = {"raw": raw_message["data"]}

                await manager.broadcast(channel, payload)

        except asyncio.CancelledError:
            logger.info("Redis relay task cancelled.")
            return
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Redis relay encountered an error, reconnecting in 5 s: %s", exc
            )
            await asyncio.sleep(5)
