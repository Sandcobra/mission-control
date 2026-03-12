from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Agent, AgentRun, Task, TaskEvent
from app.schemas.metrics import CostMetrics, FailureMetrics, OverviewMetrics


async def get_overview_metrics(db: AsyncSession) -> OverviewMetrics:
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    # Agent counts by status (one query)
    agent_counts_result = await db.execute(
        select(Agent.status, func.count(Agent.id)).group_by(Agent.status)
    )
    agent_counts: dict[str, int] = {row[0]: row[1] for row in agent_counts_result}
    agents_total = sum(agent_counts.values())
    agents_idle = agent_counts.get("idle", 0)
    agents_running_count = agent_counts.get("running", 0)
    agents_blocked_count = agent_counts.get("blocked", 0)
    agents_offline = agent_counts.get("offline", 0)
    agents_error = agent_counts.get("error", 0)
    agents_online = agents_total - agents_offline

    # Task counts by status (one query)
    task_counts_result = await db.execute(
        select(Task.status, func.count(Task.id)).group_by(Task.status)
    )
    task_counts: dict[str, int] = {row[0]: row[1] for row in task_counts_result}
    tasks_total = sum(task_counts.values())
    tasks_queued = task_counts.get("queued", 0)
    tasks_running = task_counts.get("running", 0)
    tasks_blocked = task_counts.get("blocked", 0)
    tasks_failed_total = task_counts.get("failed", 0)
    tasks_completed_total = task_counts.get("completed", 0)

    # Failed today
    failed_today_result = await db.execute(
        select(func.count(Task.id)).where(
            Task.status == "failed",
            Task.completed_at >= today_start,
        )
    )
    tasks_failed_24h: int = failed_today_result.scalar_one() or 0

    # Completed today
    completed_today_result = await db.execute(
        select(func.count(Task.id)).where(
            Task.status == "completed",
            Task.completed_at >= today_start,
        )
    )
    tasks_completed_24h: int = completed_today_result.scalar_one() or 0

    # Spend today
    spend_today_result = await db.execute(
        select(func.coalesce(func.sum(AgentRun.estimated_cost_usd), 0.0)).where(
            AgentRun.started_at >= today_start
        )
    )
    spend_today_usd: float = float(spend_today_result.scalar_one() or 0.0)

    # Spend total
    spend_total_result = await db.execute(
        select(func.coalesce(func.sum(AgentRun.estimated_cost_usd), 0.0))
    )
    spend_total_usd: float = float(spend_total_result.scalar_one() or 0.0)

    return OverviewMetrics(
        agents_total=agents_total,
        agents_online=agents_online,
        agents_idle=agents_idle,
        agents_running=agents_running_count,
        agents_blocked=agents_blocked_count,
        agents_offline=agents_offline,
        agents_error=agents_error,
        tasks_total=tasks_total,
        tasks_queued=tasks_queued,
        tasks_running=tasks_running,
        tasks_blocked=tasks_blocked,
        tasks_failed_24h=tasks_failed_24h,
        tasks_completed_24h=tasks_completed_24h,
        tasks_failed_total=tasks_failed_total,
        tasks_completed_total=tasks_completed_total,
        spend_today_usd=spend_today_usd,
        spend_total_usd=spend_total_usd,
    )


async def get_cost_metrics(db: AsyncSession) -> CostMetrics:
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    # Cost by agent
    by_agent_result = await db.execute(
        select(
            Agent.id.label("agent_id"),
            Agent.agent_key.label("agent_key"),
            Agent.name.label("agent_name"),
            func.coalesce(func.sum(AgentRun.estimated_cost_usd), 0.0).label("cost_usd"),
            func.coalesce(func.sum(AgentRun.token_input), 0).label("input_tokens"),
            func.coalesce(func.sum(AgentRun.token_output), 0).label("output_tokens"),
            func.count(AgentRun.id).label("run_count"),
        )
        .outerjoin(AgentRun, AgentRun.agent_id == Agent.id)
        .group_by(Agent.id, Agent.agent_key, Agent.name)
        .order_by(func.coalesce(func.sum(AgentRun.estimated_cost_usd), 0.0).desc())
    )
    by_agent: list[dict[str, Any]] = [
        {
            "agent_id": str(row.agent_id),
            "agent_key": row.agent_key,
            "agent_name": row.agent_name,
            "cost_usd": float(row.cost_usd),
            "input_tokens": int(row.input_tokens),
            "output_tokens": int(row.output_tokens),
            "run_count": int(row.run_count),
        }
        for row in by_agent_result
    ]

    # Cost by day (last 30 days)
    by_day_result = await db.execute(
        select(
            func.date_trunc("day", AgentRun.started_at).label("day"),
            func.coalesce(func.sum(AgentRun.estimated_cost_usd), 0.0).label("cost_usd"),
            func.coalesce(func.sum(AgentRun.token_input), 0).label("input_tokens"),
            func.coalesce(func.sum(AgentRun.token_output), 0).label("output_tokens"),
            func.count(AgentRun.id).label("task_count"),
        )
        .where(AgentRun.started_at >= datetime.utcnow() - timedelta(days=30))
        .group_by(text("day"))
        .order_by(text("day asc"))
    )
    by_day: list[dict[str, Any]] = [
        {
            "date": row.day.date().isoformat() if row.day else None,
            "cost_usd": float(row.cost_usd),
            "input_tokens": int(row.input_tokens),
            "output_tokens": int(row.output_tokens),
            "task_count": int(row.task_count),
        }
        for row in by_day_result
    ]

    # Total
    total_result = await db.execute(
        select(func.coalesce(func.sum(AgentRun.estimated_cost_usd), 0.0))
    )
    total_usd: float = float(total_result.scalar_one() or 0.0)

    # Today
    today_result = await db.execute(
        select(func.coalesce(func.sum(AgentRun.estimated_cost_usd), 0.0)).where(
            AgentRun.started_at >= today_start
        )
    )
    today_usd: float = float(today_result.scalar_one() or 0.0)

    return CostMetrics(
        total_usd=total_usd,
        today_usd=today_usd,
        by_day=by_day,
        by_agent=by_agent,
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

    # Top error message patterns
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
