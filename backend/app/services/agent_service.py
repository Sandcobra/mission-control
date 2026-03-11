from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Agent, AgentHeartbeat
from app.schemas.agents import AgentHeartbeatRequest, AgentRegisterRequest


async def register_agent(db: AsyncSession, data: AgentRegisterRequest) -> Agent:
    """
    Upsert an agent record identified by agent_key.

    If the key already exists the existing row is updated with the latest
    registration data and status set to 'idle'.  Otherwise a new row is
    inserted.
    """
    result = await db.execute(select(Agent).where(Agent.agent_key == data.agent_key))
    agent: Optional[Agent] = result.scalar_one_or_none()

    now = datetime.utcnow()

    if agent is None:
        agent = Agent(
            id=uuid.uuid4(),
            agent_key=data.agent_key,
            name=data.name,
            runtime_type=data.runtime_type,
            role=data.role,
            model_provider=data.model_provider,
            model_name=data.model_name,
            status="idle",
            host=data.host,
            version=data.version,
            created_at=now,
            updated_at=now,
            metadata_=data.metadata,
        )
        db.add(agent)
    else:
        agent.name = data.name
        agent.runtime_type = data.runtime_type
        agent.role = data.role
        agent.model_provider = data.model_provider
        agent.model_name = data.model_name
        agent.status = "idle"
        agent.host = data.host
        agent.version = data.version
        agent.updated_at = now
        agent.metadata_ = data.metadata

    await db.flush()
    await db.refresh(agent)
    return agent


async def record_heartbeat(db: AsyncSession, data: AgentHeartbeatRequest) -> Agent:
    """
    Update the agent's last_heartbeat timestamp and status, and insert an
    AgentHeartbeat row for historical tracking.
    """
    result = await db.execute(select(Agent).where(Agent.agent_key == data.agent_key))
    agent: Optional[Agent] = result.scalar_one_or_none()

    if agent is None:
        raise ValueError(f"Agent with key '{data.agent_key}' not found.")

    now = datetime.utcnow()
    agent.last_heartbeat = now
    agent.status = data.status
    agent.updated_at = now

    heartbeat = AgentHeartbeat(
        id=uuid.uuid4(),
        agent_id=agent.id,
        status=data.status,
        cpu_percent=data.cpu_percent,
        memory_mb=data.memory_mb,
        queue_depth=data.queue_depth,
        created_at=now,
        payload=data.payload,
    )
    db.add(heartbeat)

    await db.flush()
    await db.refresh(agent)
    return agent


async def get_agent(db: AsyncSession, agent_id: uuid.UUID) -> Optional[Agent]:
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    return result.scalar_one_or_none()


async def get_agent_by_key(db: AsyncSession, agent_key: str) -> Optional[Agent]:
    result = await db.execute(select(Agent).where(Agent.agent_key == agent_key))
    return result.scalar_one_or_none()


async def list_agents(
    db: AsyncSession, status: Optional[str] = None
) -> list[Agent]:
    query = select(Agent).order_by(Agent.created_at.desc())
    if status is not None:
        query = query.where(Agent.status == status)
    result = await db.execute(query)
    return list(result.scalars().all())


async def mark_stale_agents(
    db: AsyncSession, threshold_seconds: int = 120
) -> None:
    """
    Mark agents as 'offline' when their last heartbeat is older than
    threshold_seconds, or when last_heartbeat has never been recorded.
    """
    cutoff = datetime.utcnow() - timedelta(seconds=threshold_seconds)

    await db.execute(
        update(Agent)
        .where(
            (Agent.last_heartbeat < cutoff) | (Agent.last_heartbeat.is_(None))
        )
        .where(Agent.status != "offline")
        .values(status="offline", updated_at=datetime.utcnow())
    )
    await db.flush()
