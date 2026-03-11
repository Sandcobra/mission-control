"""
openclaw_example.py - Demonstrates the OpenClaw wrapper and MC_EVENT protocol.

This file has two parts:

  PART A - The wrapper invocation
    Shows how to call openclaw_wrapper.py from the command line (or via
    subprocess) to monitor an OpenClaw job.

  PART B - The child job script
    Shows how an OpenClaw (or any) job emits structured MC_EVENT lines so
    the wrapper can forward them to Mission Control in real time.

----------------------------------------------------------------------
PART A - Launching via command line
----------------------------------------------------------------------

Install the SDK:
    pip install -e ./agent-sdk/python

Then run any job through the wrapper:

    mc-openclaw \\
        --base-url   http://localhost:8000 \\
        --api-key    agent-key-1 \\
        --agent-key  openclaw-worker-01 \\
        --agent-name "OpenClaw Worker 01" \\
        --task-key   "nba-research-2026-03-11" \\
        --task-title "NBA Research 2026-03-11" \\
        -- python my_openclaw_job.py --date 2026-03-11

Or invoke the module directly:

    python -m mission_control_client.openclaw_wrapper \\
        --api-key agent-key-1 \\
        --agent-key openclaw-worker-01 \\
        --task-key nba-001 \\
        --task-title "NBA Research" \\
        -- python my_openclaw_job.py

----------------------------------------------------------------------
PART B - Emitting MC_EVENT lines from a child job
----------------------------------------------------------------------

The child process can emit structured events to Mission Control simply by
printing lines that begin with ``MC_EVENT:`` followed by a JSON object.
All other stdout lines are captured and forwarded as log events.

MC_EVENT JSON schema:
    {
        "type":    "<event_type>",   // required
        "message": "<string>",       // optional human-readable summary
        "payload": { ... }           // optional structured data
        // Shorthand fields (promoted to payload automatically):
        "percent":   <int>,          // shorthand for progress_updated
        "tool_name": "<string>",     // shorthand for tool_called / tool_result_received
        "args":      { ... },        // tool call arguments
        "result":    "<string>",     // tool result summary
        "reason":    "<string>"      // shorthand for task_blocked
    }

Supported event types:
    progress_updated      Updates the progress bar in the dashboard.
    tool_called           Records a tool invocation.
    tool_result_received  Records a tool result.
    task_blocked          Pauses the task pending external input.
    log                   Forwards a structured log message.
    <any_custom_type>     Forwarded verbatim to Mission Control.
"""

from __future__ import annotations

import asyncio
import json
import sys
import time


# ---------------------------------------------------------------------------
# MC_EVENT helper (copy this into your own job scripts)
# ---------------------------------------------------------------------------


def mc_event(event_type: str, message: str | None = None, **payload) -> None:
    """
    Emit a structured Mission Control event to stdout.

    The wrapper process reads these lines and forwards them to the
    Mission Control API in real time.

    Args:
        event_type: One of the well-known types or a custom string.
        message: Optional human-readable summary.
        **payload: Arbitrary key/value data included in the event payload.

    Examples:
        mc_event("progress_updated", "Fetching games", percent=25)
        mc_event("tool_called", tool_name="fetch_odds", args={"date": "2026-03-11"})
        mc_event("tool_result_received", tool_name="fetch_odds", result="ok")
        mc_event("log", "Debug: found 12 games")
    """
    obj: dict = {"type": event_type}
    if message:
        obj["message"] = message
    if payload:
        obj["payload"] = payload
    # The MC_EVENT: prefix must be on the same line as the JSON.
    print("MC_EVENT:" + json.dumps(obj, separators=(",", ":")), flush=True)


# ---------------------------------------------------------------------------
# Simulated OpenClaw job (PART B)
# ---------------------------------------------------------------------------
# This is what a child job script might look like.
# Run it directly to see the events it would emit:
#
#     python openclaw_example.py --run-job
#
# Or run it through the wrapper to see Mission Control receive the events:
#
#     mc-openclaw \
#         --api-key agent-key-1 \
#         --agent-key openclaw-01 \
#         --task-key demo-001 \
#         --task-title "Demo Job" \
#         -- python openclaw_example.py --run-job
# ---------------------------------------------------------------------------


async def simulated_openclaw_job() -> None:
    """
    Simulates an OpenClaw research job that emits structured MC_EVENT lines.

    In a real job this would be replaced with actual LLM calls, web scraping,
    odds API requests, etc.
    """
    start = time.monotonic()

    # Step 1 - Initialise
    mc_event("progress_updated", "Initialising job", percent=0, current_step="init")
    await asyncio.sleep(0.3)

    # Step 2 - Fetch game schedule
    mc_event("tool_called", "Fetching NBA schedule", tool_name="fetch_schedule", args={"date": "2026-03-11", "league": "NBA"})
    await asyncio.sleep(0.5)
    mc_event("tool_result_received", "Fetched 12 games", tool_name="fetch_schedule", result="12 games found")
    mc_event("progress_updated", "Schedule loaded", percent=20, current_step="fetch_schedule")

    # Step 3 - Fetch odds for each game
    games = [f"game_{i}" for i in range(1, 5)]
    for idx, game_id in enumerate(games, start=1):
        mc_event(
            "tool_called",
            f"Fetching odds for {game_id}",
            tool_name="fetch_odds",
            args={"game_id": game_id, "markets": ["h2h", "spreads"]},
        )
        await asyncio.sleep(0.2)
        mc_event(
            "tool_result_received",
            f"Odds fetched for {game_id}",
            tool_name="fetch_odds",
            result=f"moneyline: -110/+100, spread: -3.5/-3.5",
        )
        pct = 20 + int(idx / len(games) * 40)
        mc_event("progress_updated", f"Fetched odds {idx}/{len(games)}", percent=pct, current_step="fetch_odds")

    # Step 4 - Run model inference
    mc_event("tool_called", "Running prediction model", tool_name="run_model", args={"model": "edge_v2", "games": len(games)})
    await asyncio.sleep(0.8)
    mc_event("tool_result_received", "Model inference complete", tool_name="run_model", result="4 predictions generated")
    mc_event("progress_updated", "Predictions ready", percent=80, current_step="model_inference")

    # Step 5 - Write output
    mc_event("tool_called", "Writing report", tool_name="write_report", args={"format": "csv"})
    await asyncio.sleep(0.2)
    mc_event("tool_result_received", "Report written", tool_name="write_report", result="outputs/slate_2026-03-11.csv")
    mc_event("progress_updated", "Report written", percent=95, current_step="write_report")

    # Regular stdout lines are captured as log events
    print("All done! Report available at outputs/slate_2026-03-11.csv", flush=True)

    elapsed = time.monotonic() - start
    mc_event("progress_updated", "Job complete", percent=100, current_step="done")
    mc_event("log", f"Job finished in {elapsed:.2f}s", elapsed_seconds=round(elapsed, 2))


# ---------------------------------------------------------------------------
# Entry point for --run-job mode
# ---------------------------------------------------------------------------


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Simulated OpenClaw job with MC_EVENT output.")
    parser.add_argument("--run-job", action="store_true", help="Run the simulated job.")
    args = parser.parse_args()

    if args.run_job:
        asyncio.run(simulated_openclaw_job())
        sys.exit(0)

    # If not running as a job, print usage examples
    print(__doc__)


if __name__ == "__main__":
    main()
