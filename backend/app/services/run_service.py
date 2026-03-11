from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AgentRun
from app.schemas.runs import RunCostUpdateRequest, RunCreateRequest


async def create_run(db: AsyncSession, data: RunCreateRequest) -> AgentRun:
    now = datetime.utcnow()
    run = AgentRun(
        id=uuid.uuid4(),
        agent_id=data.agent_id,
        task_id=data.task_id,
        run_status="running",
        started_at=now,
    )
    db.add(run)
    await db.flush()
    await db.refresh(run)
    return run


async def update_run_cost(
    db: AsyncSession, run_id: uuid.UUID, data: RunCostUpdateRequest
) -> AgentRun:
    result = await db.execute(select(AgentRun).where(AgentRun.id == run_id))
    run: Optional[AgentRun] = result.scalar_one_or_none()
    if run is None:
        raise ValueError(f"Run {run_id} not found.")

    now = datetime.utcnow()

    if data.token_input is not None:
        run.token_input = data.token_input
    if data.token_output is not None:
        run.token_output = data.token_output
    if data.estimated_cost_usd is not None:
        run.estimated_cost_usd = data.estimated_cost_usd
    if data.run_status is not None:
        run.run_status = data.run_status
        if data.run_status in ("completed", "failed", "cancelled") and run.ended_at is None:
            run.ended_at = now

    await db.flush()
    await db.refresh(run)
    return run


async def get_run(db: AsyncSession, run_id: uuid.UUID) -> Optional[AgentRun]:
    result = await db.execute(select(AgentRun).where(AgentRun.id == run_id))
    return result.scalar_one_or_none()
