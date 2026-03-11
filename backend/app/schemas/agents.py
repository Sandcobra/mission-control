from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class AgentRegisterRequest(BaseModel):
    agent_key: str = Field(..., description="Unique identifier key for the agent.")
    name: str = Field(..., description="Human-readable agent name.")
    runtime_type: str = Field(..., description="E.g. 'docker', 'k8s', 'process'.")
    role: str = Field(..., description="Agent role, e.g. 'worker', 'orchestrator'.")
    model_provider: str = Field(..., description="LLM provider, e.g. 'openai', 'anthropic'.")
    model_name: str = Field(..., description="Model identifier, e.g. 'gpt-4o'.")
    host: str = Field(..., description="Hostname or IP where the agent is running.")
    version: str = Field(..., description="Agent software version string.")
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentHeartbeatRequest(BaseModel):
    agent_key: str = Field(..., description="Unique key identifying the agent.")
    status: str = Field(..., description="Current agent status, e.g. 'idle', 'busy'.")
    cpu_percent: Optional[float] = Field(None, ge=0, le=100)
    memory_mb: Optional[float] = Field(None, ge=0)
    queue_depth: Optional[int] = Field(None, ge=0)
    payload: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class AgentResponse(BaseModel):
    id: uuid.UUID
    agent_key: str
    name: str
    runtime_type: str
    role: str
    model_provider: str
    model_name: str
    status: str
    current_task_id: Optional[uuid.UUID] = None
    last_heartbeat: Optional[datetime] = None
    host: str
    version: str
    created_at: datetime
    updated_at: datetime
    metadata: Optional[dict[str, Any]] = None

    model_config = {"from_attributes": True}


class AgentListResponse(BaseModel):
    items: list[AgentResponse]
    total: int
