from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Agent, Artifact, Task, TaskEvent
from app.schemas.tasks import (
    ArtifactCreateRequest,
    TaskCreateRequest,
    TaskEventRequest,
    TaskUpdateRequest,
)

# Task statuses that imply terminal / special state transitions
_EVENT_STATUS_MAP: dict[str, str] = {
    "task_completed": "completed",
    "task_failed": "failed",
    "task_blocked": "blocked",
    "task_started": "running",
    "task_cancelled": "cancelled",
}


async def create_task(db: AsyncSession, data: TaskCreateRequest) -> Task:
    now = datetime.utcnow()
    task = Task(
        id=uuid.uuid4(),
        task_key=data.task_key,
        title=data.title,
        description=data.description,
        status="queued",
        priority=data.priority,
        parent_task_id=data.parent_task_id,
        created_at=now,
        updated_at=now,
        metadata_=data.metadata,
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


async def assign_task(
    db: AsyncSession, task_id: uuid.UUID, agent_id: uuid.UUID
) -> Task:
    result = await db.execute(select(Task).where(Task.id == task_id))
    task: Optional[Task] = result.scalar_one_or_none()
    if task is None:
        raise ValueError(f"Task {task_id} not found.")

    agent_result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent: Optional[Agent] = agent_result.scalar_one_or_none()
    if agent is None:
        raise ValueError(f"Agent {agent_id} not found.")

    now = datetime.utcnow()
    task.assigned_agent_id = agent_id
    task.status = "running"
    if task.started_at is None:
        task.started_at = now
    task.updated_at = now

    agent.current_task_id = task_id
    agent.status = "running"
    agent.updated_at = now

    await db.flush()
    await db.refresh(task)
    return task


async def add_task_event(
    db: AsyncSession, task_id: uuid.UUID, data: TaskEventRequest
) -> TaskEvent:
    result = await db.execute(select(Task).where(Task.id == task_id))
    task: Optional[Task] = result.scalar_one_or_none()
    if task is None:
        raise ValueError(f"Task {task_id} not found.")

    # Resolve agent from key if provided
    agent_id: Optional[uuid.UUID] = None
    if data.agent_key:
        agent_result = await db.execute(
            select(Agent).where(Agent.agent_key == data.agent_key)
        )
        agent = agent_result.scalar_one_or_none()
        if agent is not None:
            agent_id = agent.id

    now = datetime.utcnow()
    event = TaskEvent(
        id=uuid.uuid4(),
        task_id=task_id,
        agent_id=agent_id,
        event_type=data.event_type,
        message=data.message,
        payload=data.payload,
        created_at=now,
    )
    db.add(event)

    # Apply status side-effects based on event type
    new_status = _EVENT_STATUS_MAP.get(data.event_type.lower())
    if new_status:
        task.status = new_status
        task.updated_at = now
        if new_status in ("completed", "failed", "cancelled"):
            task.completed_at = now
            # Release agent from task
            if task.assigned_agent_id:
                await db.execute(
                    update(Agent)
                    .where(Agent.id == task.assigned_agent_id)
                    .values(current_task_id=None, status="idle", updated_at=now)
                )

    # Persist progress/step if provided in payload
    payload = data.payload or {}
    if "progress_percent" in payload:
        task.progress_percent = payload["progress_percent"]
        task.updated_at = now
    if "current_step" in payload:
        task.current_step = payload["current_step"]
        task.updated_at = now
    if "result_summary" in payload:
        task.result_summary = payload["result_summary"]
        task.updated_at = now
    if "error_message" in payload:
        task.error_message = payload["error_message"]
        task.updated_at = now

    await db.flush()
    await db.refresh(event)
    return event


async def add_artifact(
    db: AsyncSession, task_id: uuid.UUID, data: ArtifactCreateRequest
) -> Artifact:
    result = await db.execute(select(Task).where(Task.id == task_id))
    if result.scalar_one_or_none() is None:
        raise ValueError(f"Task {task_id} not found.")

    now = datetime.utcnow()
    artifact = Artifact(
        id=uuid.uuid4(),
        task_id=task_id,
        artifact_type=data.artifact_type,
        name=data.name,
        uri=data.uri,
        size_bytes=data.size_bytes,
        created_at=now,
        metadata_=data.metadata,
    )
    db.add(artifact)
    await db.flush()
    await db.refresh(artifact)
    return artifact


async def get_task(db: AsyncSession, task_id: uuid.UUID) -> Optional[Task]:
    result = await db.execute(select(Task).where(Task.id == task_id))
    return result.scalar_one_or_none()


async def list_tasks(
    db: AsyncSession,
    status: Optional[str] = None,
    agent_id: Optional[uuid.UUID] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Task]:
    query = select(Task).order_by(Task.created_at.desc()).limit(limit).offset(offset)
    if status is not None:
        query = query.where(Task.status == status)
    if agent_id is not None:
        query = query.where(Task.assigned_agent_id == agent_id)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_task_events(db: AsyncSession, task_id: uuid.UUID) -> list[TaskEvent]:
    result = await db.execute(
        select(TaskEvent)
        .where(TaskEvent.task_id == task_id)
        .order_by(TaskEvent.created_at.asc())
    )
    return list(result.scalars().all())


async def get_task_artifacts(db: AsyncSession, task_id: uuid.UUID) -> list[Artifact]:
    result = await db.execute(
        select(Artifact)
        .where(Artifact.task_id == task_id)
        .order_by(Artifact.created_at.asc())
    )
    return list(result.scalars().all())


async def update_task(
    db: AsyncSession, task_id: uuid.UUID, data: TaskUpdateRequest
) -> Task:
    result = await db.execute(select(Task).where(Task.id == task_id))
    task: Optional[Task] = result.scalar_one_or_none()
    if task is None:
        raise ValueError(f"Task {task_id} not found.")

    now = datetime.utcnow()
    changed = False

    if data.status is not None:
        task.status = data.status
        changed = True
        if data.status in ("completed", "failed", "cancelled") and task.completed_at is None:
            task.completed_at = now
        if data.status == "running" and task.started_at is None:
            task.started_at = now

    if data.progress_percent is not None:
        task.progress_percent = data.progress_percent
        changed = True
    if data.current_step is not None:
        task.current_step = data.current_step
        changed = True
    if data.result_summary is not None:
        task.result_summary = data.result_summary
        changed = True
    if data.error_message is not None:
        task.error_message = data.error_message
        changed = True

    if changed:
        task.updated_at = now

    await db.flush()
    await db.refresh(task)
    return task
