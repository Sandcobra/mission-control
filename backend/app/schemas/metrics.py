from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class OverviewMetrics(BaseModel):
    agents_total: int
    agents_online: int
    agents_idle: int
    agents_running: int
    agents_blocked: int
    agents_offline: int
    agents_error: int
    tasks_total: int
    tasks_queued: int
    tasks_running: int
    tasks_blocked: int
    tasks_failed_24h: int
    tasks_completed_24h: int
    tasks_failed_total: int
    tasks_completed_total: int
    spend_today_usd: float
    spend_total_usd: float


class CostMetrics(BaseModel):
    total_usd: float
    today_usd: float
    by_day: list[dict[str, Any]]
    by_agent: list[dict[str, Any]]


class FailureMetrics(BaseModel):
    recent_failures: list[dict[str, Any]]
    failure_count_24h: int
    top_error_types: list[dict[str, Any]]
