from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import case, cast, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID

from app.db.models import Agent, AgentRun, Task, TaskEvent
from app.schemas.metrics import CostMetrics, FailureMetrics, OverviewMetrics


async def get_overview_metrics(db: AsyncSession) -> OverviewMetrics:
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    # Agents online (non-offline)
    agents_online_result = await db.execute(
        select(func.count(Agent.id)).where(Agent.status != "offline")
    )
    total_agents_online: int = agents_online_result.scalar_one() or 0

    # Running tasks
    running_result = await db.execute(
        select(func.count(Task.id)).where(Task.status == "running")
    )
    tasks_running: int = running_result.scalar_one() or 0

    # Blocked tasks
    blocked_result = await db.execute(
        select(func.count(Task.id)).where(Task.status == "blocked")
    )
    tasks_blocked: int = blocked_result.scalar_one() or 0

    # Failed today
    failed_today_result = await db.execute(
        select(func.count(Task.id)).where(
            Task.status == "failed",
            Task.completed_at >= today_start,
        )
    )
    tasks_failed_today: int = failed_today_result.scalar_one() or 0

    # Completed today
    completed_today_result = await db.execute(
        select(func.count(Task.id)).where(
            Task.status == "completed",
            Task.completed_at >= today_start,
        )
    )
    tasks_completed_today: int = completed_today_result.scalar_one() or 0

    # Spend today
    spend_result = await db.execute(
        select(func.coalesce(func.sum(AgentRun.estimated_cost_usd), 0.0)).where(
            AgentRun.started_at >= today_start
        )
    )
    spend_today_usd: float = float(spend_result.scalar_one() or 0.0)

    # Average task duration for completed tasks (in minutes)
    avg_duration_result = await db.execute(
        select(
            func.avg(
                func.extract(
                    "epoch",
                    Task.completed_at - Task.started_at,
                )
            )
        ).where(
            Task.status == "completed",
            Task.started_at.isnot(None),
            Task.completed_at.isnot(None),
        )
    )
    avg_seconds = avg_duration_result.scalar_one()
    avg_task_duration_minutes: float | None = (
        float(avg_seconds) / 60.0 if avg_seconds is not None else None
    )

    return OverviewMetrics(
        total_agents_online=total_agents_online,
        tasks_running=tasks_running,
        tasks_blocked=tasks_blocked,
        tasks_failed_today=tasks_failed_today,
        tasks_completed_today=tasks_completed_today,
        spend_today_usd=spend_today_usd,
        avg_task_duration_minutes=avg_task_duration_minutes,
    )


async def get_cost_metrics(db: AsyncSession) -> CostMetrics:
    # Cost by agent
    by_agent_result = await db.execute(
        select(
            Agent.id.label("agent_id"),
            Agent.name.label("agent_name"),
            func.coalesce(func.sum(AgentRun.estimated_cost_usd), 0.0).label("total_usd"),
            func.coalesce(func.sum(AgentRun.token_input), 0).label("total_token_input"),
            func.coalesce(func.sum(AgentRun.token_output), 0).label("total_token_output"),
            func.count(AgentRun.id).label("run_count"),
        )
        .outerjoin(AgentRun, AgentRun.agent_id == Agent.id)
        .group_by(Agent.id, Agent.name)
        .order_by(func.coalesce(func.sum(AgentRun.estimated_cost_usd), 0.0).desc())
    )
    by_agent: list[dict[str, Any]] = [
        {
            "agent_id": str(row.agent_id),
            "agent_name": row.agent_name,
            "total_usd": float(row.total_usd),
            "total_token_input": int(row.total_token_input),
            "total_token_output": int(row.total_token_output),
            "run_count": int(row.run_count),
        }
        for row in by_agent_result
    ]

    # Cost by task
    by_task_result = await db.execute(
        select(
            Task.id.label("task_id"),
            Task.title.label("task_title"),
            func.coalesce(func.sum(AgentRun.estimated_cost_usd), 0.0).label("total_usd"),
        )
        .outerjoin(AgentRun, AgentRun.task_id == Task.id)
        .group_by(Task.id, Task.title)
        .order_by(func.coalesce(func.sum(AgentRun.estimated_cost_usd), 0.0).desc())
        .limit(50)
    )
    by_task: list[dict[str, Any]] = [
        {
            "task_id": str(row.task_id),
            "task_title": row.task_title,
            "total_usd": float(row.total_usd),
        }
        for row in by_task_result
    ]

    # Cost by day (last 30 days)
    by_day_result = await db.execute(
        select(
            func.date_trunc("day", AgentRun.started_at).label("day"),
            func.coalesce(func.sum(AgentRun.estimated_cost_usd), 0.0).label("total_usd"),
            func.count(AgentRun.id).label("run_count"),
        )
        .where(AgentRun.started_at >= datetime.utcnow() - timedelta(days=30))
        .group_by(text("day"))
        .order_by(text("day asc"))
    )
    by_day: list[dict[str, Any]] = [
        {
            "day": row.day.isoformat() if row.day else None,
            "total_usd": float(row.total_usd),
            "run_count": int(row.run_count),
        }
        for row in by_day_result
    ]

    # Total
    total_result = await db.execute(
        select(func.coalesce(func.sum(AgentRun.estimated_cost_usd), 0.0))
    )
    total_usd: float = float(total_result.scalar_one() or 0.0)

    return CostMetrics(
        by_agent=by_agent,
        by_task=by_task,
        by_day=by_day,
        total_usd=total_usd,
    )


async def get_failure_metrics(db: AsyncSession) -> FailureMetrics:
    since_24h = datetime.utcnow() - timedelta(hours=24)

    # Count of failures in last 24 h
    failure_count_result = await db.execute(
        select(func.count(Task.id)).where(
            Task.status == "failed",
            Task.completed_at >= since_24h,
        )
    )
    failure_count_24h: int = failure_count_result.scalar_one() or 0

    # Recent failures (last 20)
    recent_failures_result = await db.execute(
        select(
            Task.id,
            Task.task_key,
            Task.title,
            Task.error_message,
            Task.completed_at,
            Task.assigned_agent_id,
        )
        .where(Task.status == "failed")
        .order_by(Task.completed_at.desc().nulls_last())
        .limit(20)
    )
    recent_failures: list[dict[str, Any]] = [
        {
            "task_id": str(row.id),
            "task_key": row.task_key,
            "title": row.title,
            "error_message": row.error_message,
            "failed_at": row.completed_at.isoformat() if row.completed_at else None,
            "assigned_agent_id": str(row.assigned_agent_id) if row.assigned_agent_id else None,
        }
        for row in recent_failures_result
    ]

    # Top error message patterns (group by first 120 chars of error_message)
    top_errors_result = await db.execute(
        select(
            func.substring(Task.error_message, 1, 120).label("error_snippet"),
            func.count(Task.id).label("count"),
        )
        .where(Task.status == "failed", Task.error_message.isnot(None))
        .group_by(text("error_snippet"))
        .order_by(func.count(Task.id).desc())
        .limit(10)
    )
    top_error_types: list[dict[str, Any]] = [
        {
            "error_snippet": row.error_snippet,
            "count": int(row.count),
        }
        for row in top_errors_result
    ]

    return FailureMetrics(
        recent_failures=recent_failures,
        failure_count_24h=failure_count_24h,
        top_error_types=top_error_types,
    )
