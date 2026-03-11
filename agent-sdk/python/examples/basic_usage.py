"""
basic_usage.py - Complete working example of the Mission Control Python SDK.

Run against a local Mission Control instance:

    python basic_usage.py

Environment variables (all optional, defaults shown):
    MC_BASE_URL   http://localhost:8000
    MC_API_KEY    agent-key-1
"""

from __future__ import annotations

import asyncio
import logging
import os
import time

from mission_control_client import MissionControlClient
from mission_control_client.decorators import mc_task, mc_tool

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("basic_usage")

MC_BASE_URL = os.getenv("MC_BASE_URL", "http://localhost:8000")
MC_API_KEY = os.getenv("MC_API_KEY", "agent-key-1")


# ---------------------------------------------------------------------------
# Helper: a pretend tool
# ---------------------------------------------------------------------------


async def _fetch_nba_games(date: str) -> list[dict]:
    """Simulate a slow external API call."""
    await asyncio.sleep(0.5)
    return [
        {"game_id": "g1", "home": "Lakers", "away": "Celtics", "date": date},
        {"game_id": "g2", "home": "Warriors", "away": "Bulls", "date": date},
    ]


# ---------------------------------------------------------------------------
# Example 1 — manual task lifecycle
# ---------------------------------------------------------------------------


async def example_manual_lifecycle(mc: MissionControlClient) -> None:
    """Demonstrates full manual control over each lifecycle step."""
    logger.info("=== Example 1: Manual Lifecycle ===")

    # 1. Create a task
    task = await mc.create_task(
        task_key="nba-slate-2026-03-11",
        title="Research NBA Slate 2026-03-11",
        description="Fetch game schedule and odds for tonight's NBA slate.",
        priority=7,
        metadata={"league": "NBA", "date": "2026-03-11"},
    )
    task_id = task["id"]
    logger.info("Task created: id=%s", task_id)

    # 2. Assign the task to this agent
    await mc.assign_task(task_id)

    # 3. Create a run for cost tracking
    run = await mc.create_run(task_id=task_id)
    run_id = run["id"]

    # 4. Signal that work has begun
    await mc.task_started(task_id)

    # 5. Emit a tool_called event before invoking a tool
    await mc.tool_called(task_id, "fetch_nba_games", args={"date": "2026-03-11"})
    games = await _fetch_nba_games("2026-03-11")
    await mc.tool_result(task_id, "fetch_nba_games", result_summary=f"{len(games)} games fetched")

    # 6. Report incremental progress
    await mc.update_progress(task_id, percent=50, current_step="Fetching odds", message="Games loaded, fetching odds")

    # Simulate more work
    await asyncio.sleep(0.3)
    await mc.update_progress(task_id, percent=90, current_step="Generating report", message="Odds loaded")

    # 7. Upload an artifact (e.g. a generated CSV)
    await mc.upload_artifact(
        task_id=task_id,
        artifact_type="csv",
        name="nba_slate_2026-03-11.csv",
        uri="s3://my-bucket/outputs/nba_slate_2026-03-11.csv",
        size_bytes=4096,
        metadata={"row_count": len(games)},
    )

    # 8. Record LLM cost
    await mc.update_cost(
        run_id=run_id,
        token_input=1200,
        token_output=450,
        estimated_cost_usd=0.0037,
    )

    # 9. Mark the task complete
    await mc.complete_task(task_id, result_summary=f"Processed {len(games)} games for 2026-03-11.")
    logger.info("Task %s complete.", task_id)


# ---------------------------------------------------------------------------
# Example 2 — using the @mc_task decorator
# ---------------------------------------------------------------------------


async def example_decorator(mc: MissionControlClient) -> None:
    """Demonstrates the @mc_task decorator for automatic lifecycle management."""
    logger.info("=== Example 2: @mc_task Decorator ===")

    @mc_task(
        mc,
        task_key="decorator-demo-001",
        title="Decorator Demo Task",
        description="Shows the @mc_task decorator handling lifecycle automatically.",
        priority=5,
    )
    async def analyse_games(games: list[dict], task_id: str = None) -> str:
        logger.info("analyse_games running with task_id=%s", task_id)

        # Wrap tool call with the decorator
        @mc_tool(mc, task_id=task_id)
        async def score_game(game: dict) -> float:
            await asyncio.sleep(0.1)
            return 0.85  # simulated confidence score

        scores = []
        for i, game in enumerate(games):
            score = await score_game(game)
            scores.append(score)
            pct = int((i + 1) / len(games) * 100)
            await mc.update_progress(task_id, percent=pct, current_step=f"Scored game {i + 1}/{len(games)}")

        return f"Scored {len(scores)} games, avg confidence {sum(scores) / len(scores):.2f}"

    games = [
        {"game_id": "g1", "home": "Lakers", "away": "Celtics"},
        {"game_id": "g2", "home": "Warriors", "away": "Bulls"},
        {"game_id": "g3", "home": "Heat", "away": "Bucks"},
    ]
    result = await analyse_games(games)
    logger.info("Decorator task result: %s", result)


# ---------------------------------------------------------------------------
# Example 3 — error handling
# ---------------------------------------------------------------------------


async def example_error_handling(mc: MissionControlClient) -> None:
    """Demonstrates how fail_task is called on exception."""
    logger.info("=== Example 3: Error Handling ===")

    task = await mc.create_task(
        task_key="failing-task-001",
        title="Task That Will Fail",
        priority=3,
    )
    task_id = task["id"]
    await mc.assign_task(task_id)
    await mc.task_started(task_id)

    try:
        await asyncio.sleep(0.1)
        raise ValueError("Simulated downstream API timeout")
    except ValueError as exc:
        await mc.fail_task(
            task_id,
            error_message=str(exc),
            error_type="ValueError",
            retryable=True,
        )
        logger.info("Task %s marked as failed (expected).", task_id)


# ---------------------------------------------------------------------------
# Example 4 — blocked task
# ---------------------------------------------------------------------------


async def example_blocked_task(mc: MissionControlClient) -> None:
    """Demonstrates blocking a task pending human approval."""
    logger.info("=== Example 4: Blocked Task ===")

    task = await mc.create_task(
        task_key="approval-required-001",
        title="Awaiting Human Approval",
        priority=6,
    )
    task_id = task["id"]
    await mc.assign_task(task_id)
    await mc.task_started(task_id)
    await mc.update_progress(task_id, percent=40, current_step="Awaiting approval")

    await mc.block_task(
        task_id,
        reason="Requires human sign-off on high-confidence bet before placing wager.",
    )
    logger.info("Task %s blocked, waiting for approval.", task_id)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main() -> None:
    start = time.monotonic()

    async with MissionControlClient(
        base_url=MC_BASE_URL,
        api_key=MC_API_KEY,
        agent_key="example-agent-01",
        name="Example Research Agent",
        runtime_type="custom",
        role="researcher",
        model_provider="anthropic",
        model_name="claude-sonnet-4-6",
        version="1.0.0",
    ) as mc:
        logger.info("Agent registered: id=%s", mc.agent_id)

        await example_manual_lifecycle(mc)
        await example_decorator(mc)
        await example_error_handling(mc)
        await example_blocked_task(mc)

    elapsed = time.monotonic() - start
    logger.info("All examples completed in %.2fs.", elapsed)


if __name__ == "__main__":
    asyncio.run(main())
