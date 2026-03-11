"""
OpenClaw Mission Control Wrapper

Wraps any subprocess (typically an OpenClaw job) and reports its execution
lifecycle to Mission Control.

Usage:
    python openclaw_wrapper.py \\
        --base-url http://localhost:8000 \\
        --api-key agent-key-1 \\
        --agent-key openclaw-worker-01 \\
        --agent-name "OpenClaw Worker 01" \\
        --task-key "task-001" \\
        --task-title "NBA Research" \\
        -- python openclaw_job.py --league nba

Structured event protocol (MC_EVENT):
    Any line written to stdout by the child process that begins with the
    literal prefix ``MC_EVENT:`` followed by a JSON object is interpreted
    as a structured Mission Control event.  All other lines are buffered as
    log output and emitted periodically as progress_updated events.

    MC_EVENT JSON schema:
        {
            "type": "<event_type>",     // required, e.g. "progress_updated"
            "message": "<string>",      // optional human-readable message
            "payload": { ... }          // optional structured payload
        }

    Built-in shorthand fields (merged into payload automatically):
        "percent"      -> emitted as progress_updated
        "tool_name"    -> emitted as tool_called or tool_result_received
                          depending on whether "args" or "result" is present

    Example emissions from the child process (Python):
        import json, sys

        def mc_event(type_, message=None, **payload):
            obj = {"type": type_}
            if message:
                obj["message"] = message
            if payload:
                obj["payload"] = payload
            print("MC_EVENT:" + json.dumps(obj), flush=True)

        mc_event("progress_updated", message="Fetching odds", percent=25)
        mc_event("tool_called", tool_name="fetch_odds", args={"game_id": "123"})
        mc_event("tool_result_received", tool_name="fetch_odds", result="ok")
        mc_event("log", message="Some informational message")
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from typing import List

from .client import MissionControlClient, MissionControlError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("openclaw_wrapper")

# Prefix that child processes write to stdout to emit structured events
MC_EVENT_PREFIX = "MC_EVENT:"

# How often (seconds) to flush buffered log lines as a progress event
LOG_FLUSH_INTERVAL = 15

# How many log lines to include per progress event
LOG_BATCH_SIZE = 20


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mission Control wrapper for OpenClaw (or any) subprocess.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--base-url", default="http://localhost:8000", help="Mission Control base URL.")
    parser.add_argument("--api-key", required=True, help="Mission Control API key.")
    parser.add_argument("--agent-key", required=True, help="Stable agent identifier.")
    parser.add_argument("--agent-name", default="OpenClaw Agent", help="Human-readable agent name.")
    parser.add_argument("--runtime-type", default="openclaw", help="Runtime type tag.")
    parser.add_argument("--role", default="worker", help="Agent role tag.")
    parser.add_argument("--model-provider", default="unknown", help="Model provider.")
    parser.add_argument("--model-name", default="unknown", help="Model name.")
    parser.add_argument("--task-key", required=True, help="Stable task identifier.")
    parser.add_argument("--task-title", required=True, help="Human-readable task title.")
    parser.add_argument("--task-description", default=None, help="Optional task description.")
    parser.add_argument("--priority", type=int, default=5, help="Task priority 1-10.")
    parser.add_argument(
        "--heartbeat-interval",
        type=int,
        default=30,
        help="Seconds between heartbeats.",
    )
    # Everything after -- is the child command
    parser.add_argument("child_command", nargs=argparse.REMAINDER)
    return parser


async def run(args: argparse.Namespace) -> int:
    """
    Core async runner.

    Returns the child process exit code.
    """
    child_command: List[str] = args.child_command
    # Strip leading '--' separator if present
    if child_command and child_command[0] == "--":
        child_command = child_command[1:]

    if not child_command:
        logger.error("No child command specified after '--'.")
        return 2

    async with MissionControlClient(
        base_url=args.base_url,
        api_key=args.api_key,
        agent_key=args.agent_key,
        name=args.agent_name,
        runtime_type=args.runtime_type,
        role=args.role,
        model_provider=args.model_provider,
        model_name=args.model_name,
    ) as mc:
        # Create and assign the task
        task = await mc.create_task(
            task_key=args.task_key,
            title=args.task_title,
            description=args.task_description,
            priority=args.priority,
        )
        task_id: str = task["id"]
        logger.info("Task created: id=%s key=%s", task_id, args.task_key)

        await mc.assign_task(task_id)
        await mc.task_started(task_id)

        # Spawn the child process
        logger.info("Spawning child: %s", " ".join(child_command))
        try:
            proc = await asyncio.create_subprocess_exec(
                *child_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError as exc:
            await mc.fail_task(
                task_id,
                error_message=f"Child process not found: {exc}",
                error_type="FileNotFoundError",
                retryable=False,
            )
            return 1

        log_buffer: List[str] = []
        structured_events_seen = False
        exit_code: int = 0

        async def flush_logs() -> None:
            """Emit buffered log lines as a progress event."""
            if not log_buffer:
                return
            batch = log_buffer[:LOG_BATCH_SIZE]
            del log_buffer[:LOG_BATCH_SIZE]
            message = "\n".join(batch)
            try:
                await mc.emit_event(
                    task_id,
                    event_type="log_output",
                    message=message,
                    payload={"lines": batch},
                )
            except MissionControlError:
                logger.warning("Failed to flush log buffer.", exc_info=True)

        async def handle_event_line(line: str) -> None:
            """Parse and forward a structured MC_EVENT line."""
            json_str = line[len(MC_EVENT_PREFIX):].strip()
            try:
                obj = json.loads(json_str)
            except json.JSONDecodeError:
                logger.warning("Malformed MC_EVENT JSON: %r", json_str)
                return

            event_type: str = obj.get("type", "unknown")
            message: str | None = obj.get("message")
            payload: dict = obj.get("payload", {})

            # Convenience: top-level shorthand fields merged into payload
            for shorthand in ("percent", "tool_name", "args", "result", "reason"):
                if shorthand in obj and shorthand not in payload:
                    payload[shorthand] = obj[shorthand]

            # Dispatch to specialised helpers where available
            try:
                if event_type == "progress_updated":
                    percent = payload.get("percent", 0)
                    current_step = payload.get("current_step")
                    await mc.update_progress(task_id, percent, current_step=current_step, message=message)
                elif event_type == "tool_called":
                    await mc.tool_called(task_id, payload.get("tool_name", "unknown"), args=payload.get("args"))
                elif event_type == "tool_result_received":
                    await mc.tool_result(task_id, payload.get("tool_name", "unknown"), result_summary=message)
                elif event_type == "task_blocked":
                    await mc.block_task(task_id, reason=message or payload.get("reason", "blocked"))
                elif event_type == "log":
                    # Structured log lines are forwarded as log_output events
                    await mc.emit_event(task_id, "log_output", message=message, payload=payload)
                else:
                    # Generic passthrough
                    await mc.emit_event(task_id, event_type, message=message, payload=payload)
            except MissionControlError:
                logger.warning("Failed to forward MC_EVENT type=%s.", event_type, exc_info=True)

        async def read_stdout() -> None:
            """Continuously read child stdout and dispatch lines."""
            nonlocal structured_events_seen
            assert proc.stdout is not None
            async for raw_line in proc.stdout:
                line = raw_line.decode(errors="replace").rstrip("\n")
                if line.startswith(MC_EVENT_PREFIX):
                    structured_events_seen = True
                    await handle_event_line(line)
                else:
                    # Echo to our own stdout so Docker/CI logs still show child output
                    print(line, flush=True)
                    log_buffer.append(line)
                    if len(log_buffer) >= LOG_BATCH_SIZE:
                        await flush_logs()

        async def read_stderr() -> None:
            """Echo child stderr to our own stderr."""
            assert proc.stderr is not None
            async for raw_line in proc.stderr:
                line = raw_line.decode(errors="replace").rstrip("\n")
                print(line, file=sys.stderr, flush=True)

        async def periodic_flush() -> None:
            """Flush log buffer every LOG_FLUSH_INTERVAL seconds."""
            while True:
                await asyncio.sleep(LOG_FLUSH_INTERVAL)
                await flush_logs()

        flush_task = asyncio.create_task(periodic_flush())

        try:
            await asyncio.gather(read_stdout(), read_stderr())
            exit_code = await proc.wait()
        finally:
            flush_task.cancel()
            try:
                await flush_task
            except asyncio.CancelledError:
                pass

        # Flush any remaining buffered lines
        while log_buffer:
            await flush_logs()

        # Report final outcome
        if exit_code == 0:
            await mc.complete_task(task_id, result_summary="Child process exited successfully.")
            logger.info("Task completed successfully.")
        else:
            await mc.fail_task(
                task_id,
                error_message=f"Child process exited with code {exit_code}.",
                error_type="non_zero_exit",
                retryable=exit_code not in (1, 2),
            )
            logger.warning("Task failed with exit code %d.", exit_code)

        return exit_code


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        exit_code = asyncio.run(run(args))
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
        exit_code = 130

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
