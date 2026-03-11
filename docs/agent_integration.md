# Mission Control — Agent Integration Guide

This guide covers every way an agent can integrate with Mission Control,
from the high-level Python SDK to raw HTTP calls in any language.

---

## Quick Start — Python SDK

### 1. Install

```bash
pip install mission-control-client
# or from source:
pip install -e ./agent-sdk/python
```

### 2. Register and run a task

```python
import asyncio
from mission_control_client import MissionControlClient

async def main():
    async with MissionControlClient(
        base_url="http://localhost:8000",
        api_key="your-api-key",
        agent_key="my-agent-01",          # stable, unique identifier
        name="My Research Agent",
        runtime_type="custom",
        role="researcher",
        model_provider="anthropic",
        model_name="claude-sonnet-4-6",
    ) as mc:
        # mc.agent_id is now populated
        task = await mc.create_task("research-001", "Research NBA Slate")
        task_id = task["id"]

        await mc.assign_task(task_id)
        await mc.task_started(task_id)

        await mc.tool_called(task_id, "fetch_schedule", args={"date": "2026-03-11"})
        # ... do real work here ...
        await mc.tool_result(task_id, "fetch_schedule", result_summary="12 games loaded")

        await mc.update_progress(task_id, percent=50, current_step="fetch_odds")

        await mc.complete_task(task_id, result_summary="All done.")

asyncio.run(main())
```

### 3. Use the @mc_task decorator

The decorator automatically creates the task, assigns it, emits `task_started`,
and calls `complete_task` or `fail_task` based on whether the function raises.

```python
from mission_control_client.decorators import mc_task, mc_tool

@mc_task(mc, task_key="nba-001", title="NBA Research", priority=7)
async def research(date: str, task_id: str = None) -> str:
    """task_id is injected by the decorator."""

    @mc_tool(mc, task_id=task_id)
    async def fetch(d: str) -> list:
        ...  # real implementation

    games = await fetch(date)
    await mc.update_progress(task_id, 100, "Done")
    return f"Processed {len(games)} games"
```

### 4. Cost tracking

```python
run = await mc.create_run(task_id=task_id)

# after your LLM calls:
await mc.update_cost(
    run_id=run["id"],
    token_input=1500,
    token_output=600,
    estimated_cost_usd=0.0045,
)
```

---

## OpenClaw Wrapper

For agents that run as standalone scripts (e.g. OpenClaw jobs), the wrapper
handles all Mission Control communication on their behalf.

### Installation

```bash
pip install mission-control-client
```

This installs the `mc-openclaw` CLI entry point.

### Usage

```bash
mc-openclaw \
    --base-url   http://localhost:8000 \
    --api-key    your-api-key \
    --agent-key  openclaw-worker-01 \
    --agent-name "OpenClaw Worker 01" \
    --task-key   "nba-2026-03-11" \
    --task-title "NBA Research 2026-03-11" \
    -- python my_job.py --date 2026-03-11
```

Everything after `--` is the child command.  The wrapper:

1. Registers an agent and creates the task.
2. Spawns the child process.
3. Reads its stdout line by line.
4. Forwards `MC_EVENT:` lines to Mission Control in real time.
5. Buffers plain stdout as log events.
6. Marks the task completed or failed based on the child's exit code.

---

## MC_EVENT Protocol

Any process can emit structured events simply by writing to stdout.  Lines
that begin with `MC_EVENT:` followed by a JSON object are intercepted by the
wrapper and forwarded to Mission Control.  All other lines are captured as log
events.

### JSON Schema

```json
{
  "type":    "<event_type>",    // required
  "message": "<string>",        // optional human-readable text
  "payload": { }                // optional structured data
}
```

Shorthand top-level fields (promoted to `payload` automatically):

| Field | Shorthand for |
|---|---|
| `"percent": <int>` | `payload.percent` in `progress_updated` |
| `"tool_name": "<str>"` | `payload.tool_name` in `tool_called` / `tool_result_received` |
| `"args": { }` | `payload.args` in `tool_called` |
| `"result": "<str>"` | `payload.result` in `tool_result_received` |
| `"reason": "<str>"` | `payload.reason` in `task_blocked` |

### Python Helper

```python
import json, sys

def mc_event(type_, message=None, **payload):
    obj = {"type": type_}
    if message:
        obj["message"] = message
    if payload:
        obj["payload"] = payload
    print("MC_EVENT:" + json.dumps(obj), flush=True)

# Examples:
mc_event("progress_updated", "Loading games", percent=10, current_step="init")
mc_event("tool_called", tool_name="fetch_odds", args={"game_id": "g1"})
mc_event("tool_result_received", tool_name="fetch_odds", result="ok")
mc_event("task_blocked", reason="Awaiting human approval")
mc_event("log", "Some debug information here")
```

### JavaScript / Node.js Helper

```javascript
function mcEvent(type, message, payload = {}) {
  const obj = { type };
  if (message) obj.message = message;
  if (Object.keys(payload).length) obj.payload = payload;
  process.stdout.write("MC_EVENT:" + JSON.stringify(obj) + "\n");
}

mcEvent("progress_updated", "Fetching odds", { percent: 30, current_step: "fetch_odds" });
mcEvent("tool_called", null, { tool_name: "web_search", args: { query: "NBA tonight" } });
mcEvent("task_blocked", "Awaiting approval");
```

### Bash / curl Helper

```bash
mc_event() {
  local type="$1"
  local message="$2"
  printf 'MC_EVENT:{"type":"%s","message":"%s"}\n' "$type" "$message"
}

mc_event "progress_updated" "Starting analysis"
mc_event "log" "Found 12 games"
mc_event "task_completed" "All done"
```

---

## Raw HTTP Integration (Any Language)

All Mission Control communication is plain HTTPS.  Here are the key calls with
curl examples.

### Authentication

All requests require a Bearer token:

```
Authorization: Bearer <your-api-key>
```

### Register agent

```bash
curl -X POST http://localhost:8000/api/agents/register \
  -H "Authorization: Bearer agent-key-1" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_key":      "my-agent-01",
    "name":           "My Agent",
    "runtime_type":   "custom",
    "role":           "researcher",
    "model_provider": "anthropic",
    "model_name":     "claude-sonnet-4-6",
    "host":           "worker-01",
    "version":        "1.0.0"
  }'
```

### Create a task

```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Authorization: Bearer agent-key-1" \
  -H "Content-Type: application/json" \
  -d '{
    "task_key": "nba-001",
    "title":    "NBA Research",
    "priority": 7
  }'
```

### Emit an event

```bash
TASK_ID="<uuid from create_task>"

curl -X POST "http://localhost:8000/api/tasks/$TASK_ID/events" \
  -H "Authorization: Bearer agent-key-1" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "progress_updated",
    "message":    "Fetching odds",
    "payload":    {"percent": 50, "current_step": "fetch_odds"}
  }'
```

### Send a heartbeat

```bash
curl -X POST http://localhost:8000/api/agents/heartbeat \
  -H "Authorization: Bearer agent-key-1" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id":   "<uuid from register>",
    "cpu_percent": 23.4,
    "memory_mb":   512
  }'
```

---

## Heartbeat Requirements

Agents MUST send a heartbeat at least every **60 seconds** to be considered
online.  The Python SDK's `start_heartbeat_loop(interval=30)` satisfies this
automatically.

If no heartbeat is received within 60 seconds the backend marks the agent
`status = "offline"` and broadcasts that change to the dashboard.

The heartbeat payload is optional beyond `agent_id`:

```json
{
  "agent_id":    "uuid",
  "agent_key":   "my-agent-01",
  "cpu_percent": 34.2,
  "memory_mb":   512,
  "queue_depth": 3
}
```

---

## Cost Tracking

Record LLM usage by associating a run with a task and then posting costs:

```python
# At the start of a task
run = await mc.create_run(task_id=task_id)

# After each LLM call (or aggregate at the end)
await mc.update_cost(
    run_id=run["id"],
    token_input=1200,
    token_output=450,
    estimated_cost_usd=0.0037,
)
```

Costs are aggregated per task and per agent in the dashboard.  The formula for
`estimated_cost_usd` is agent-determined; Mission Control stores the value as
reported.

---

## Artifact Registration

Register files produced by a task so the dashboard can display download links:

```python
await mc.upload_artifact(
    task_id=task_id,
    artifact_type="csv",
    name="nba_slate_2026-03-11.csv",
    uri="s3://my-bucket/outputs/nba_slate_2026-03-11.csv",
    size_bytes=4096,
    metadata={"row_count": 48},
)
```

The artifact data itself is not transmitted to Mission Control; only its
metadata and URI are stored.  The dashboard renders a link to the URI.
