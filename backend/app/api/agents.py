from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import verify_agent_api_key
from app.db.base import get_db
from app.events.redis_bus import publish_agent_event
from app.schemas.agents import (
    AgentHeartbeatRequest,
    AgentListResponse,
    AgentRegisterRequest,
    AgentResponse,
)
from app.services import agent_service


class _AgentOfflineRequest(BaseModel):
    agent_key: str
    agent_id: Optional[str] = None

router = APIRouter(prefix="/api/agents", tags=["agents"])


def _agent_to_response(agent) -> AgentResponse:
    return AgentResponse(
        id=agent.id,
        agent_key=agent.agent_key,
        name=agent.name,
        runtime_type=agent.runtime_type,
        role=agent.role,
        model_provider=agent.model_provider,
        model_name=agent.model_name,
        status=agent.status,
        current_task_id=agent.current_task_id,
        last_heartbeat=agent.last_heartbeat,
        host=agent.host,
        version=agent.version,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
        metadata=agent.metadata_,
    )


@router.post(
    "/register",
    response_model=AgentResponse,
    status_code=status.HTTP_200_OK,
    summary="Register or re-register an agent",
)
async def register_agent(
    body: AgentRegisterRequest,
    _key: str = Depends(verify_agent_api_key),
    db: AsyncSession = Depends(get_db),
) -> AgentResponse:
    agent = await agent_service.register_agent(db, body)
    event = {
        "event": "agent_registered",
        "agent_id": str(agent.id),
        "agent_key": agent.agent_key,
        "name": agent.name,
        "status": agent.status,
    }
    await publish_agent_event(str(agent.id), event)
    return _agent_to_response(agent)


@router.post(
    "/heartbeat",
    response_model=AgentResponse,
    status_code=status.HTTP_200_OK,
    summary="Record an agent heartbeat",
)
async def agent_heartbeat(
    body: AgentHeartbeatRequest,
    _key: str = Depends(verify_agent_api_key),
    db: AsyncSession = Depends(get_db),
) -> AgentResponse:
    try:
        agent = await agent_service.record_heartbeat(db, body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    event = {
        "event": "agent_heartbeat",
        "agent_id": str(agent.id),
        "agent_key": agent.agent_key,
        "status": agent.status,
        "last_heartbeat": agent.last_heartbeat.isoformat() if agent.last_heartbeat else None,
    }
    await publish_agent_event(str(agent.id), event)
    return _agent_to_response(agent)


@router.get(
    "/",
    response_model=AgentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all agents",
)
async def list_agents(
    status: Optional[str] = Query(None, description="Filter by agent status"),
    db: AsyncSession = Depends(get_db),
) -> AgentListResponse:
    agents = await agent_service.list_agents(db, status=status)
    return AgentListResponse(
        items=[_agent_to_response(a) for a in agents],
        total=len(agents),
    )


@router.get(
    "/{agent_id}",
    response_model=AgentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a single agent by ID",
)
async def get_agent(
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> AgentResponse:
    agent = await agent_service.get_agent(db, agent_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found.",
        )
    return _agent_to_response(agent)


@router.post(
    "/offline",
    response_model=AgentResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark an agent as offline",
)
async def set_agent_offline(
    body: _AgentOfflineRequest,
    _key: str = Depends(verify_agent_api_key),
    db: AsyncSession = Depends(get_db),
) -> AgentResponse:
    agent = await agent_service.get_agent_by_key(db, body.agent_key)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found.")
    heartbeat_data = AgentHeartbeatRequest(agent_key=body.agent_key, status="offline")
    agent = await agent_service.record_heartbeat(db, heartbeat_data)
    await publish_agent_event(
        str(agent.id),
        {"event": "agent_offline", "agent_id": str(agent.id), "agent_key": agent.agent_key},
    )
    return _agent_to_response(agent)
