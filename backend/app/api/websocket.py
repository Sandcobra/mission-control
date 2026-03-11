from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.events.websocket_manager import manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])

# Channels that the Redis relay will subscribe to by default.
# Per-entity channels (e.g. "agent:<uuid>", "task:<uuid>") are forwarded
# automatically because publish_agent_event / publish_task_event also publish
# to these global channels.
DEFAULT_RELAY_CHANNELS = [
    "agent_updates",
    "task_updates",
]


@router.websocket("/ws/{channel}")
async def websocket_endpoint(websocket: WebSocket, channel: str) -> None:
    """
    WebSocket endpoint that clients connect to for real-time updates.

    ``channel`` can be any of:
    - ``agent_updates``     – all agent registration / heartbeat events
    - ``task_updates``      – all task lifecycle events
    - ``agent:<uuid>``      – events for a specific agent
    - ``task:<uuid>``       – events for a specific task
    """
    await manager.connect(websocket, channel)
    logger.info("WS client connected to channel '%s'", channel)
    try:
        while True:
            # Keep the connection alive; the server is push-only on this
            # endpoint, but we still need to drain client frames to detect
            # disconnects.
            data = await websocket.receive_text()
            # Optionally echo pings back as a keep-alive signal.
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        logger.info("WS client disconnected from channel '%s'", channel)
    finally:
        manager.disconnect(websocket, channel)
