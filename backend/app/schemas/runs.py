from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class RunCreateRequest(BaseModel):
    agent_id: uuid.UUID = Field(..., description="Agent executing this run.")
    task_id: Optional[uuid.UUID] = None


class RunCostUpdateRequest(BaseModel):
    token_input: Optional[int] = Field(None, ge=0)
    token_output: Optional[int] = Field(None, ge=0)
    estimated_cost_usd: Optional[float] = Field(None, ge=0)
    run_status: Optional[str] = None


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class RunResponse(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    task_id: Optional[uuid.UUID] = None
    run_status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    token_input: Optional[int] = None
    token_output: Optional[int] = None
    estimated_cost_usd: Optional[float] = None
    metadata: Optional[dict[str, Any]] = None

    model_config = {"from_attributes": True}
