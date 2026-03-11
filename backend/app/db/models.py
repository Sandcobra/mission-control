from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    BigInteger,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_key: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    runtime_type: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    model_provider: Mapped[str] = mapped_column(Text, nullable=False)
    model_name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="offline", server_default="offline")
    current_task_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    last_heartbeat: Mapped[Optional[datetime]] = mapped_column(
        nullable=True
    )
    host: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    metadata_: Mapped[Optional[dict[str, Any]]] = mapped_column(
        "metadata", JSON, nullable=True, default=dict
    )

    # Relationships
    tasks: Mapped[list["Task"]] = relationship(
        "Task", back_populates="assigned_agent", foreign_keys="Task.assigned_agent_id"
    )
    heartbeats: Mapped[list["AgentHeartbeat"]] = relationship(
        "AgentHeartbeat", back_populates="agent"
    )
    runs: Mapped[list["AgentRun"]] = relationship("AgentRun", back_populates="agent")
    task_events: Mapped[list["TaskEvent"]] = relationship(
        "TaskEvent", back_populates="agent"
    )
    artifacts: Mapped[list["Artifact"]] = relationship("Artifact", back_populates="agent")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    task_key: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default="queued", server_default="queued"
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=5, server_default="5")
    assigned_agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True
    )
    parent_task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True
    )
    progress_percent: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    current_step: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    metadata_: Mapped[Optional[dict[str, Any]]] = mapped_column(
        "metadata", JSON, nullable=True, default=dict
    )

    # Relationships
    assigned_agent: Mapped[Optional["Agent"]] = relationship(
        "Agent", back_populates="tasks", foreign_keys=[assigned_agent_id]
    )
    parent_task: Mapped[Optional["Task"]] = relationship(
        "Task", remote_side="Task.id", foreign_keys=[parent_task_id]
    )
    child_tasks: Mapped[list["Task"]] = relationship(
        "Task", back_populates="parent_task", foreign_keys=[parent_task_id]
    )
    events: Mapped[list["TaskEvent"]] = relationship(
        "TaskEvent", back_populates="task", order_by="TaskEvent.created_at"
    )
    artifacts: Mapped[list["Artifact"]] = relationship(
        "Artifact", back_populates="task"
    )
    runs: Mapped[list["AgentRun"]] = relationship("AgentRun", back_populates="task")


class TaskEvent(Base):
    __tablename__ = "task_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True
    )
    event_type: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payload: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), default=datetime.utcnow
    )

    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="events")
    agent: Mapped[Optional["Agent"]] = relationship("Agent", back_populates="task_events")


class AgentHeartbeat(Base):
    __tablename__ = "agent_heartbeats"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(Text, nullable=False)
    cpu_percent: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    memory_mb: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    queue_depth: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), default=datetime.utcnow
    )
    payload: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    agent: Mapped["Agent"] = relationship("Agent", back_populates="heartbeats")


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True
    )
    artifact_type: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    uri: Mapped[str] = mapped_column(Text, nullable=False)
    size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), default=datetime.utcnow
    )
    metadata_: Mapped[Optional[dict[str, Any]]] = mapped_column(
        "metadata", JSON, nullable=True
    )

    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="artifacts")
    agent: Mapped[Optional["Agent"]] = relationship("Agent", back_populates="artifacts")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True
    )
    run_status: Mapped[str] = mapped_column(
        Text, nullable=False, default="running", server_default="running"
    )
    started_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), default=datetime.utcnow
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    token_input: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    token_output: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    estimated_cost_usd: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 4), nullable=True
    )
    metadata_: Mapped[Optional[dict[str, Any]]] = mapped_column(
        "metadata", JSON, nullable=True
    )

    # Relationships
    agent: Mapped["Agent"] = relationship("Agent", back_populates="runs")
    task: Mapped[Optional["Task"]] = relationship("Task", back_populates="runs")
