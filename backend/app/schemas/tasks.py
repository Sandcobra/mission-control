from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class TaskCreateRequest(BaseModel):
    task_key: str = Field(..., description="Unique business key for the task.")
    title: str = Field(..., description="Short human-readable title.")
    description: Optional[str] = None
    priority: int = Field(default=5, ge=1, le=10)
    parent_task_id: Optional[uuid.UUID] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskAssignRequest(BaseModel):
    agent_id: uuid.UUID = Field(..., description="ID of the agent to assign the task to.")


class TaskUpdateRequest(BaseModel):
    status: Optional[str] = None
    progress_percent: Optional[float] = Field(None, ge=0, le=100)
    current_step: Optional[str] = None
    result_summary: Optional[str] = None
    error_message: Optional[str] = None


class TaskEventRequest(BaseModel):
    agent_key: Optional[str] = None
    event_type: str = Field(..., description="Event type, e.g. 'task_started', 'step_complete'.")
    message: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)


class ArtifactCreateRequest(BaseModel):
    artifact_type: str = Field(..., description="E.g. 'file', 'report', 'image'.")
    name: str
    uri: str = Field(..., description="Location URI for the artifact.")
    size_bytes: Optional[int] = Field(None, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class TaskResponse(BaseModel):
    id: uuid.UUID
    task_key: str
    title: str
    description: Optional[str] = None
    status: str
    priority: int
    assigned_agent_id: Optional[uuid.UUID] = None
    parent_task_id: Optional[uuid.UUID] = None
    progress_percent: Optional[float] = None
    current_step: Optional[str] = None
    result_summary: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    metadata: Optional[dict[str, Any]] = None

    model_config = {"from_attributes": True}


class TaskEventResponse(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    agent_id: Optional[uuid.UUID] = None
    event_type: str
    message: Optional[str] = None
    payload: Optional[dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ArtifactResponse(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    agent_id: Optional[uuid.UUID] = None
    artifact_type: str
    name: str
    uri: str
    size_bytes: Optional[int] = None
    created_at: datetime
    metadata: Optional[dict[str, Any]] = None

    model_config = {"from_attributes": True}


class TaskDetailResponse(BaseModel):
    task: TaskResponse
    events: list[TaskEventResponse]
    artifacts: list[ArtifactResponse]
