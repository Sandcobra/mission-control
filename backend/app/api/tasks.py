from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import verify_agent_api_key
from app.db.base import get_db
from app.events.redis_bus import publish_task_event
from app.schemas.tasks import (
    ArtifactCreateRequest,
    ArtifactResponse,
    TaskAssignRequest,
    TaskCreateRequest,
    TaskDetailResponse,
    TaskEventRequest,
    TaskEventResponse,
    TaskResponse,
    TaskUpdateRequest,
)
from app.services import task_service

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def _task_to_response(task) -> TaskResponse:
    return TaskResponse(
        id=task.id,
        task_key=task.task_key,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        assigned_agent_id=task.assigned_agent_id,
        parent_task_id=task.parent_task_id,
        progress_percent=float(task.progress_percent) if task.progress_percent is not None else None,
        current_step=task.current_step,
        result_summary=task.result_summary,
        error_message=task.error_message,
        started_at=task.started_at,
        completed_at=task.completed_at,
        created_at=task.created_at,
        updated_at=task.updated_at,
        metadata=task.metadata_,
    )


def _event_to_response(event) -> TaskEventResponse:
    return TaskEventResponse(
        id=event.id,
        task_id=event.task_id,
        agent_id=event.agent_id,
        event_type=event.event_type,
        message=event.message,
        payload=event.payload,
        created_at=event.created_at,
    )


def _artifact_to_response(artifact) -> ArtifactResponse:
    return ArtifactResponse(
        id=artifact.id,
        task_id=artifact.task_id,
        agent_id=artifact.agent_id,
        artifact_type=artifact.artifact_type,
        name=artifact.name,
        uri=artifact.uri,
        size_bytes=artifact.size_bytes,
        created_at=artifact.created_at,
        metadata=artifact.metadata_,
    )


@router.post(
    "/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
)
async def create_task(
    body: TaskCreateRequest,
    _key: str = Depends(verify_agent_api_key),
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    task = await task_service.create_task(db, body)
    await publish_task_event(
        str(task.id),
        {"event": "task_created", "task_id": str(task.id), "task_key": task.task_key, "status": task.status},
    )
    return _task_to_response(task)


@router.post(
    "/{task_id}/assign",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Assign a task to an agent",
)
async def assign_task(
    task_id: uuid.UUID,
    body: TaskAssignRequest,
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    try:
        task = await task_service.assign_task(db, task_id, body.agent_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    await publish_task_event(
        str(task.id),
        {
            "event": "task_assigned",
            "task_id": str(task.id),
            "agent_id": str(body.agent_id),
            "status": task.status,
        },
    )
    return _task_to_response(task)


@router.post(
    "/{task_id}/events",
    response_model=TaskEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an event to a task",
)
async def add_task_event(
    task_id: uuid.UUID,
    body: TaskEventRequest,
    _key: str = Depends(verify_agent_api_key),
    db: AsyncSession = Depends(get_db),
) -> TaskEventResponse:
    try:
        event = await task_service.add_task_event(db, task_id, body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    await publish_task_event(
        str(task_id),
        {
            "event": "task_event",
            "task_id": str(task_id),
            "event_type": event.event_type,
            "message": event.message,
            "payload": event.payload,
        },
    )
    return _event_to_response(event)


@router.post(
    "/{task_id}/artifacts",
    response_model=ArtifactResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an artifact to a task",
)
async def add_artifact(
    task_id: uuid.UUID,
    body: ArtifactCreateRequest,
    _key: str = Depends(verify_agent_api_key),
    db: AsyncSession = Depends(get_db),
) -> ArtifactResponse:
    try:
        artifact = await task_service.add_artifact(db, task_id, body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    await publish_task_event(
        str(task_id),
        {
            "event": "artifact_added",
            "task_id": str(task_id),
            "artifact_id": str(artifact.id),
            "artifact_type": artifact.artifact_type,
            "name": artifact.name,
            "uri": artifact.uri,
        },
    )
    return _artifact_to_response(artifact)


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Update task status or progress",
)
async def update_task(
    task_id: uuid.UUID,
    body: TaskUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    try:
        task = await task_service.update_task(db, task_id, body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    await publish_task_event(
        str(task.id),
        {"event": "task_updated", "task_id": str(task.id), "status": task.status},
    )
    return _task_to_response(task)


@router.get(
    "/",
    response_model=list[TaskResponse],
    status_code=status.HTTP_200_OK,
    summary="List tasks with optional filters",
)
async def list_tasks(
    status: Optional[str] = Query(None),
    agent_id: Optional[uuid.UUID] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[TaskResponse]:
    tasks = await task_service.list_tasks(
        db, status=status, agent_id=agent_id, limit=limit, offset=offset
    )
    return [_task_to_response(t) for t in tasks]


@router.get(
    "/{task_id}",
    response_model=TaskDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get task detail with events and artifacts",
)
async def get_task_detail(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> TaskDetailResponse:
    task = await task_service.get_task(db, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found."
        )
    events = await task_service.get_task_events(db, task_id)
    artifacts = await task_service.get_task_artifacts(db, task_id)
    return TaskDetailResponse(
        task=_task_to_response(task),
        events=[_event_to_response(e) for e in events],
        artifacts=[_artifact_to_response(a) for a in artifacts],
    )


@router.get(
    "/{task_id}/events",
    response_model=list[TaskEventResponse],
    status_code=status.HTTP_200_OK,
    summary="List events for a task",
)
async def list_task_events(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[TaskEventResponse]:
    task = await task_service.get_task(db, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found."
        )
    events = await task_service.get_task_events(db, task_id)
    return [_event_to_response(e) for e in events]


@router.get(
    "/{task_id}/artifacts",
    response_model=list[ArtifactResponse],
    status_code=status.HTTP_200_OK,
    summary="List artifacts for a task",
)
async def list_task_artifacts(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[ArtifactResponse]:
    task = await task_service.get_task(db, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found."
        )
    artifacts = await task_service.get_task_artifacts(db, task_id)
    return [_artifact_to_response(a) for a in artifacts]
