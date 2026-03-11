from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class OverviewMetrics(BaseModel):
    total_agents_online: int
    tasks_running: int
    tasks_blocked: int
    tasks_failed_today: int
    tasks_completed_today: int
    spend_today_usd: float
    avg_task_duration_minutes: Optional[float] = None


class CostMetrics(BaseModel):
    by_agent: list[dict[str, Any]]
    by_task: list[dict[str, Any]]
    by_day: list[dict[str, Any]]
    total_usd: float


class FailureMetrics(BaseModel):
    recent_failures: list[dict[str, Any]]
    failure_count_24h: int
    top_error_types: list[dict[str, Any]]
