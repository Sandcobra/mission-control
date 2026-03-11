"""
Mission Control Client SDK

Usage:
    from mission_control_client import MissionControlClient

    async with MissionControlClient(
        base_url="http://localhost:8000",
        api_key="agent-key-1",
        agent_key="my-agent-01",
        name="My Research Agent",
        runtime_type="custom",
        role="researcher",
        model_provider="anthropic",
        model_name="claude-sonnet-4-6",
    ) as mc:
        task = await mc.create_task("task-001", "Research NBA slate")
        await mc.assign_task(task["id"])
        await mc.task_started(task["id"])
        await mc.update_progress(task["id"], 50, "Halfway done")
        await mc.complete_task(task["id"], "Done!")
"""

from __future__ import annotations

import asyncio
import logging
import socket
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class MissionControlError(Exception):
    """Raised when a Mission Control API call fails."""

    def __init__(self, message: str, status_code: int | None = None, response_body: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class MissionControlClient:
    """
    Async client for agents to register and report into Mission Control.

    Can be used as an async context manager:

        async with MissionControlClient(...) as mc:
            ...

    Or managed manually:

        mc = MissionControlClient(...)
        await mc.register()
        await mc.start_heartbeat_loop()
        ...
        await mc.stop_heartbeat_loop()
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        agent_key: str,
        name: str,
        runtime_type: str,
        role: str,
        model_provider: str,
        model_name: str,
        host: str | None = None,
        version: str = "1.0.0",
    ):
        """
        Args:
            base_url: Base URL of the Mission Control backend, e.g. "http://localhost:8000".
            api_key: API key used for authentication (Bearer token).
            agent_key: Unique stable identifier for this agent instance.
            name: Human-readable name for this agent.
            runtime_type: Runtime category, e.g. "custom", "langchain", "autogen".
            role: Functional role, e.g. "researcher", "writer", "orchestrator".
            model_provider: LLM provider, e.g. "anthropic", "openai".
            model_name: Model identifier, e.g. "claude-sonnet-4-6".
            host: Hostname to report; defaults to socket.gethostname().
            version: Agent code version string.
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.agent_key = agent_key
        self.name = name
        self.runtime_type = runtime_type
        self.role = role
        self.model_provider = model_provider
        self.model_name = model_name
        self.host = host or socket.gethostname()
        self.version = version

        # Populated after successful registration
        self.agent_id: str | None = None

        self._http: httpx.AsyncClient | None = None
        self._heartbeat_task: asyncio.Task | None = None

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "MissionControlClient":
        self._http = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"X-MC-API-Key": self.api_key},
            timeout=30.0,
        )
        await self.register()
        await self.start_heartbeat_loop()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.stop_heartbeat_loop()
        try:
            await self._set_offline()
        except Exception:
            logger.warning("Failed to set agent offline during exit.", exc_info=True)
        if self._http:
            await self._http.aclose()
            self._http = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _client(self) -> httpx.AsyncClient:
        if self._http is None:
            # Allow use without context manager by creating a one-shot client
            self._http = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"X-MC-API-Key": self.api_key},
                timeout=30.0,
            )
        return self._http

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        """Execute an HTTP request and return the parsed JSON body."""
        client = self._client()
        try:
            response = await client.request(method, path, **kwargs)
        except httpx.RequestError as exc:
            raise MissionControlError(f"Network error calling {method} {path}: {exc}") from exc

        if response.status_code >= 400:
            body: Any = None
            try:
                body = response.json()
            except Exception:
                body = response.text
            raise MissionControlError(
                f"API error {response.status_code} from {method} {path}",
                status_code=response.status_code,
                response_body=body,
            )

        if response.status_code == 204 or not response.content:
            return {}

        return response.json()

    async def _set_offline(self) -> None:
        """Mark this agent as offline via a dedicated endpoint or heartbeat."""
        try:
            await self._request(
                "POST",
                "/api/agents/offline",
                json={"agent_id": self.agent_id, "agent_key": self.agent_key},
            )
        except MissionControlError as exc:
            # Offline endpoint may not exist in all server versions; degrade gracefully.
            if exc.status_code == 404:
                logger.debug("Offline endpoint not found; skipping.")
            else:
                raise

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    async def register(self) -> dict:
        """
        Register this agent with Mission Control.

        POST /api/agents/register

        Populates self.agent_id on success and returns the full registration
        response payload.
        """
        payload = {
            "agent_key": self.agent_key,
            "name": self.name,
            "runtime_type": self.runtime_type,
            "role": self.role,
            "model_provider": self.model_provider,
            "model_name": self.model_name,
            "host": self.host,
            "version": self.version,
        }
        logger.info("Registering agent '%s' (%s) with Mission Control.", self.name, self.agent_key)
        data = await self._request("POST", "/api/agents/register", json=payload)
        self.agent_id = data.get("id") or data.get("agent_id")
        logger.info("Agent registered with id=%s.", self.agent_id)
        return data

    # ------------------------------------------------------------------
    # Heartbeat
    # ------------------------------------------------------------------

    async def heartbeat(
        self,
        cpu_percent: float | None = None,
        memory_mb: float | None = None,
        queue_depth: int | None = None,
    ) -> dict:
        """
        Send a heartbeat to Mission Control.

        POST /api/agents/heartbeat

        Args:
            cpu_percent: Current CPU utilisation 0-100.
            memory_mb: Resident memory in megabytes.
            queue_depth: Number of tasks queued for this agent.
        """
        payload: dict[str, Any] = {
            "agent_id": self.agent_id,
            "agent_key": self.agent_key,
        }
        if cpu_percent is not None:
            payload["cpu_percent"] = cpu_percent
        if memory_mb is not None:
            payload["memory_mb"] = memory_mb
        if queue_depth is not None:
            payload["queue_depth"] = queue_depth

        try:
            data = await self._request("POST", "/api/agents/heartbeat", json=payload)
            logger.debug("Heartbeat sent for agent_id=%s.", self.agent_id)
            return data
        except MissionControlError:
            logger.warning("Heartbeat failed for agent_id=%s.", self.agent_id, exc_info=True)
            return {}

    async def start_heartbeat_loop(self, interval: int = 30) -> None:
        """
        Start a background asyncio task that calls heartbeat() every *interval* seconds.

        Args:
            interval: Seconds between heartbeat calls. Defaults to 30.
        """
        if self._heartbeat_task and not self._heartbeat_task.done():
            logger.debug("Heartbeat loop already running.")
            return

        async def _loop() -> None:
            while True:
                await asyncio.sleep(interval)
                await self.heartbeat()

        self._heartbeat_task = asyncio.create_task(_loop())
        logger.debug("Heartbeat loop started (interval=%ds).", interval)

    async def stop_heartbeat_loop(self) -> None:
        """Cancel the background heartbeat task if it is running."""
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            logger.debug("Heartbeat loop stopped.")
        self._heartbeat_task = None

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------

    async def create_task(
        self,
        task_key: str,
        title: str,
        description: str | None = None,
        priority: int = 5,
        metadata: dict | None = None,
    ) -> dict:
        """
        Create a new task in Mission Control.

        POST /api/tasks

        Args:
            task_key: Stable external identifier, e.g. "nba-research-001".
            title: Short human-readable title.
            description: Optional longer description.
            priority: Integer priority 1-10 (higher = more urgent). Defaults to 5.
            metadata: Arbitrary key/value pairs stored with the task.

        Returns:
            The created task object as a dict.
        """
        payload: dict[str, Any] = {
            "task_key": task_key,
            "title": title,
            "priority": priority,
            "metadata": metadata or {},
        }
        if description is not None:
            payload["description"] = description

        logger.info("Creating task key='%s' title='%s'.", task_key, title)
        return await self._request("POST", "/api/tasks", json=payload)

    async def assign_task(self, task_id: str) -> dict:
        """
        Assign a task to this agent.

        POST /api/tasks/{task_id}/assign

        Args:
            task_id: The task's UUID as returned by create_task.

        Returns:
            Updated task object.
        """
        if not self.agent_id:
            raise MissionControlError("Agent is not registered. Call register() first.")

        payload = {"agent_id": self.agent_id}
        logger.info("Assigning task_id=%s to agent_id=%s.", task_id, self.agent_id)
        return await self._request("POST", f"/api/tasks/{task_id}/assign", json=payload)

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    async def emit_event(
        self,
        task_id: str,
        event_type: str,
        message: str | None = None,
        payload: dict | None = None,
    ) -> dict:
        """
        Emit a structured event for a task.

        POST /api/tasks/{task_id}/events

        Args:
            task_id: UUID of the task this event belongs to.
            event_type: One of the well-known event type strings, e.g. "task_started".
            message: Human-readable summary of the event.
            payload: Arbitrary structured data relevant to the event.

        Returns:
            The persisted event object.
        """
        body: dict[str, Any] = {
            "event_type": event_type,
            "agent_key": self.agent_key,
            "payload": payload or {},
        }
        if message is not None:
            body["message"] = message

        logger.debug("Emitting event type='%s' for task_id=%s.", event_type, task_id)
        return await self._request("POST", f"/api/tasks/{task_id}/events", json=body)

    async def task_started(self, task_id: str) -> dict:
        """
        Emit a task_started event and transition the task to running status.

        Args:
            task_id: UUID of the task.
        """
        return await self.emit_event(
            task_id,
            event_type="task_started",
            message="Task execution has begun.",
        )

    async def update_progress(
        self,
        task_id: str,
        percent: int,
        current_step: str | None = None,
        message: str | None = None,
    ) -> dict:
        """
        Emit a progress_updated event.

        Args:
            task_id: UUID of the task.
            percent: Completion percentage 0-100.
            current_step: Optional label for the current processing step.
            message: Optional human-readable status message.
        """
        payload: dict[str, Any] = {"progress_percent": percent}
        if current_step is not None:
            payload["current_step"] = current_step

        return await self.emit_event(
            task_id,
            event_type="progress_updated",
            message=message or f"Progress: {percent}%",
            payload=payload,
        )

    async def tool_called(
        self,
        task_id: str,
        tool_name: str,
        args: dict | None = None,
    ) -> dict:
        """
        Emit a tool_called event.

        Args:
            task_id: UUID of the task.
            tool_name: Name of the tool being invoked.
            args: Arguments passed to the tool (will be logged, not executed).
        """
        return await self.emit_event(
            task_id,
            event_type="tool_called",
            message=f"Calling tool: {tool_name}",
            payload={"tool_name": tool_name, "args": args or {}},
        )

    async def tool_result(
        self,
        task_id: str,
        tool_name: str,
        result_summary: str | None = None,
    ) -> dict:
        """
        Emit a tool_result_received event.

        Args:
            task_id: UUID of the task.
            tool_name: Name of the tool whose result was received.
            result_summary: Short human-readable description of the result.
        """
        return await self.emit_event(
            task_id,
            event_type="tool_result_received",
            message=result_summary or f"Tool result received from {tool_name}",
            payload={"tool_name": tool_name},
        )

    async def complete_task(
        self,
        task_id: str,
        result_summary: str | None = None,
    ) -> dict:
        """
        Mark a task as completed.

        Emits a task_completed event and then PATCHes the task status.

        Args:
            task_id: UUID of the task.
            result_summary: Human-readable description of the outcome.
        """
        await self.emit_event(
            task_id,
            event_type="task_completed",
            message=result_summary or "Task completed successfully.",
            payload={"result_summary": result_summary},
        )
        logger.info("Task task_id=%s completed.", task_id)
        return await self._request(
            "PUT",
            f"/api/tasks/{task_id}",
            json={"status": "completed", "result_summary": result_summary},
        )

    async def fail_task(
        self,
        task_id: str,
        error_message: str,
        error_type: str | None = None,
        retryable: bool = False,
    ) -> dict:
        """
        Mark a task as failed.

        Emits a task_failed event and PATCHes the task status.

        Args:
            task_id: UUID of the task.
            error_message: Description of what went wrong.
            error_type: Optional category, e.g. "timeout", "rate_limit".
            retryable: Whether Mission Control should offer to retry the task.
        """
        payload: dict[str, Any] = {
            "error_message": error_message,
            "retryable": retryable,
        }
        if error_type is not None:
            payload["error_type"] = error_type

        await self.emit_event(
            task_id,
            event_type="task_failed",
            message=error_message,
            payload=payload,
        )
        logger.warning("Task task_id=%s failed: %s", task_id, error_message)
        return await self._request(
            "PUT",
            f"/api/tasks/{task_id}",
            json={"status": "failed", "error_message": error_message},
        )

    async def block_task(self, task_id: str, reason: str) -> dict:
        """
        Mark a task as blocked pending external input.

        Args:
            task_id: UUID of the task.
            reason: Human-readable explanation of what is blocking progress.
        """
        return await self.emit_event(
            task_id,
            event_type="task_blocked",
            message=reason,
            payload={"reason": reason},
        )

    # ------------------------------------------------------------------
    # Artifacts
    # ------------------------------------------------------------------

    async def upload_artifact(
        self,
        task_id: str,
        artifact_type: str,
        name: str,
        uri: str,
        size_bytes: int | None = None,
        metadata: dict | None = None,
    ) -> dict:
        """
        Register an artifact produced by a task.

        POST /api/tasks/{task_id}/artifacts

        The artifact itself is not uploaded here; *uri* should point to wherever
        the data has already been stored (e.g. S3, GCS, local file path).

        Args:
            task_id: UUID of the task that produced the artifact.
            artifact_type: Category, e.g. "report", "csv", "model_weights".
            name: Display name for the artifact.
            uri: Location of the artifact data.
            size_bytes: File size in bytes, if known.
            metadata: Arbitrary key/value pairs.
        """
        payload: dict[str, Any] = {
            "artifact_type": artifact_type,
            "name": name,
            "uri": uri,
            "metadata": metadata or {},
        }
        if size_bytes is not None:
            payload["size_bytes"] = size_bytes

        return await self._request("POST", f"/api/tasks/{task_id}/artifacts", json=payload)

    # ------------------------------------------------------------------
    # Runs and cost tracking
    # ------------------------------------------------------------------

    async def create_run(self, task_id: str | None = None) -> dict:
        """
        Create a new agent run record.

        POST /api/runs

        A run represents one execution episode of this agent, optionally
        associated with a task.

        Args:
            task_id: UUID of the task this run serves, if any.

        Returns:
            The created run object, including its UUID.
        """
        payload: dict[str, Any] = {"agent_id": self.agent_id}
        if task_id is not None:
            payload["task_id"] = task_id

        return await self._request("POST", "/api/runs", json=payload)

    async def update_cost(
        self,
        run_id: str,
        token_input: int,
        token_output: int,
        estimated_cost_usd: float,
    ) -> dict:
        """
        Report LLM token usage and estimated cost for a run.

        POST /api/runs/{run_id}/cost

        Args:
            run_id: UUID of the run as returned by create_run.
            token_input: Number of prompt/input tokens consumed.
            token_output: Number of completion/output tokens produced.
            estimated_cost_usd: Estimated USD cost for this run.
        """
        payload = {
            "token_input": token_input,
            "token_output": token_output,
            "estimated_cost_usd": estimated_cost_usd,
        }
        return await self._request("POST", f"/api/runs/{run_id}/cost", json=payload)
