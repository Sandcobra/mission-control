"""
Decorator utilities for Mission Control task and tool tracking.

Usage:

    from mission_control_client import MissionControlClient
    from mission_control_client.decorators import mc_task, mc_tool

    @mc_task(mc, task_key="research-001", title="NBA Research")
    async def run_research(league: str):
        ...

    # Inside a task function you can decorate individual tool calls:
    @mc_tool(mc, task_id="<uuid>")
    async def fetch_odds(game_id: str):
        ...
"""

from __future__ import annotations

import asyncio
import functools
import logging
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)


def mc_task(
    mc_client,
    task_key: str,
    title: str,
    description: str | None = None,
    priority: int = 5,
    metadata: dict | None = None,
):
    """
    Class-level decorator factory that wraps an async function as a tracked
    Mission Control task.

    Behaviour:
    - Before the wrapped function runs: create_task, assign_task, task_started.
    - On successful return: complete_task with the stringified return value.
    - On exception: fail_task with the exception message.

    The wrapped function receives an extra keyword argument ``task_id`` containing
    the Mission Control task UUID so inner helpers can emit their own events.

    Args:
        mc_client: An initialised (and registered) MissionControlClient instance.
        task_key: Stable external identifier for this task.
        title: Human-readable task title.
        description: Optional longer description.
        priority: Integer priority 1-10. Defaults to 5.
        metadata: Arbitrary metadata dict stored with the task.

    Example:

        @mc_task(mc, task_key="nba-001", title="NBA slate research")
        async def research(league: str, task_id: str = None):
            await mc.update_progress(task_id, 50, "Fetching odds")
            return "Research complete"
    """

    def decorator(func: Callable[..., Coroutine]) -> Callable[..., Coroutine]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Create and configure the task
            task = await mc_client.create_task(
                task_key=task_key,
                title=title,
                description=description,
                priority=priority,
                metadata=metadata or {},
            )
            task_id: str = task["id"]

            await mc_client.assign_task(task_id)
            await mc_client.task_started(task_id)

            # Inject task_id as a keyword arg so the function can use it
            kwargs["task_id"] = task_id

            try:
                result = await func(*args, **kwargs)
            except asyncio.CancelledError:
                await mc_client.fail_task(
                    task_id,
                    error_message="Task was cancelled.",
                    error_type="cancelled",
                    retryable=True,
                )
                raise
            except Exception as exc:
                error_type = type(exc).__name__
                await mc_client.fail_task(
                    task_id,
                    error_message=str(exc),
                    error_type=error_type,
                    retryable=False,
                )
                raise
            else:
                result_summary = str(result) if result is not None else None
                await mc_client.complete_task(task_id, result_summary=result_summary)
                return result

        return wrapper

    return decorator


def mc_tool(mc_client, task_id: str):
    """
    Decorator factory that wraps an async function and emits tool_called /
    tool_result_received events around it.

    Args:
        mc_client: An initialised MissionControlClient instance.
        task_id: UUID of the active task this tool invocation belongs to.

    Example:

        @mc_tool(mc, task_id=task_id)
        async def fetch_odds(game_id: str) -> dict:
            ...
    """

    def decorator(func: Callable[..., Coroutine]) -> Callable[..., Coroutine]:
        tool_name = func.__name__

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Capture args for logging (convert to a serialisable dict where possible)
            try:
                import inspect

                sig = inspect.signature(func)
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                serialisable_args: dict[str, Any] = {
                    k: _try_serialize(v) for k, v in bound.arguments.items()
                }
            except Exception:
                serialisable_args = {}

            await mc_client.tool_called(task_id, tool_name=tool_name, args=serialisable_args)

            try:
                result = await func(*args, **kwargs)
            except Exception as exc:
                # Emit a result event noting the failure, then re-raise
                await mc_client.tool_result(
                    task_id,
                    tool_name=tool_name,
                    result_summary=f"Tool raised {type(exc).__name__}: {exc}",
                )
                raise

            result_summary = _summarize(result)
            await mc_client.tool_result(task_id, tool_name=tool_name, result_summary=result_summary)
            return result

        return wrapper

    return decorator


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _try_serialize(value: Any) -> Any:
    """Return *value* if JSON-serialisable, otherwise its repr."""
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    if isinstance(value, (list, tuple)):
        return [_try_serialize(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _try_serialize(v) for k, v in value.items()}
    return repr(value)


def _summarize(result: Any, max_len: int = 200) -> str:
    """Produce a short human-readable summary of a tool result."""
    if result is None:
        return "No result"
    text = str(result)
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text
