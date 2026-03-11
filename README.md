# Mission Control

Mission Control is a real-time observability and coordination platform for
autonomous AI agents.  It provides a central dashboard where you can monitor
every agent that is running, watch task progress events stream in live, track
LLM token costs, and inspect artifacts — all without touching the agent code
beyond a single SDK import.

---

## Quick Start

### Prerequisites

- Docker and Docker Compose

### 1. Clone and configure

```bash
git clone <repo-url>
cd mission_control
cp infra/.env.example infra/.env   # edit API keys and secrets
```

### 2. Start the full stack

```bash
docker compose -f infra/docker-compose.yml up --build
```

Services:

| Service | URL |
|---|---|
| Dashboard (frontend) | http://localhost:3000 |
| API (backend) | http://localhost:8000 |
| Nginx proxy | http://localhost:80 |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

### 3. Open the dashboard

Navigate to http://localhost in your browser.

---

## Architecture Overview

```
Agents ──HTTP──► FastAPI backend ──► PostgreSQL (persistence)
                       │
                       ├──► Redis pub/sub
                       │         │
                       └──WS──► Next.js dashboard (live updates)
                            │
                         Nginx :80
```

- **Backend** (FastAPI + SQLAlchemy) — REST ingest API, WebSocket fan-out,
  event storage.
- **Frontend** (Next.js 15 + Tailwind) — live dashboard with agent cards, task
  timelines, and cost charts.
- **PostgreSQL** — primary persistent store for all agents, tasks, events,
  runs, and artifacts.
- **Redis** — pub/sub broker that synchronises WebSocket state across backend
  instances.
- **Nginx** — reverse proxy that routes `/api/*` and `/ws/*` to the backend
  and everything else to the frontend.

See `docs/architecture.md` for the full design document.

---

## Python SDK

Install:

```bash
pip install mission-control-client
# or from source:
pip install -e ./agent-sdk/python
```

Basic usage:

```python
import asyncio
from mission_control_client import MissionControlClient

async def main():
    async with MissionControlClient(
        base_url="http://localhost:8000",
        api_key="your-api-key",
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
        await mc.update_progress(task["id"], 50, "Fetching odds")
        await mc.complete_task(task["id"], "Done!")

asyncio.run(main())
```

See `agent-sdk/python/examples/basic_usage.py` for a complete working example
covering manual task lifecycle, the `@mc_task` decorator, error handling, and
cost tracking.

### OpenClaw Wrapper

Wrap any subprocess (including OpenClaw jobs) without modifying it:

```bash
mc-openclaw \
    --api-key    your-api-key \
    --agent-key  openclaw-worker-01 \
    --task-key   "nba-2026-03-11" \
    --task-title "NBA Research" \
    -- python my_job.py --date 2026-03-11
```

The job can emit structured events by printing `MC_EVENT:` prefixed JSON:

```python
import json
def mc_event(type_, message=None, **payload):
    obj = {"type": type_}
    if message: obj["message"] = message
    if payload: obj["payload"] = payload
    print("MC_EVENT:" + json.dumps(obj), flush=True)

mc_event("progress_updated", "Fetching odds", percent=45)
mc_event("tool_called", tool_name="web_search", args={"q": "NBA tonight"})
```

See `docs/agent_integration.md` for the full integration guide.

---

## Documentation

| Document | Description |
|---|---|
| `docs/architecture.md` | System design, component breakdown, scaling |
| `docs/event_schema.md` | All event types, payloads, lifecycle diagrams |
| `docs/agent_integration.md` | Python SDK, OpenClaw wrapper, raw HTTP, MC_EVENT protocol |
| `docs/api_spec.md` | Full REST and WebSocket API reference |

---

## Dashboard

```
┌─────────────────────────────────────────────────────────────────┐
│  Mission Control                                    ● 3 online  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Agents                                                          │
│  ┌──────────────────────┐  ┌──────────────────────┐            │
│  │ ● My Research Agent  │  │ ● OpenClaw Worker 01 │            │
│  │   researcher         │  │   worker             │            │
│  │   claude-sonnet-4-6  │  │   claude-haiku-3-5   │            │
│  │   CPU 23%  MEM 512MB │  │   CPU 45%  MEM 1.2GB │            │
│  └──────────────────────┘  └──────────────────────┘            │
│                                                                  │
│  Active Tasks                                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ NBA Research 2026-03-11        ████████░░  80%  running │   │
│  │ Fetching odds — 12:01:35                                 │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
mission_control/
├── agent-sdk/
│   └── python/
│       ├── mission_control_client/
│       │   ├── __init__.py          # Package exports
│       │   ├── client.py            # MissionControlClient
│       │   ├── decorators.py        # @mc_task, @mc_tool
│       │   └── openclaw_wrapper.py  # CLI wrapper for subprocesses
│       ├── examples/
│       │   ├── basic_usage.py       # Full SDK walkthrough
│       │   └── openclaw_example.py  # MC_EVENT protocol demo
│       └── setup.py
├── backend/                         # FastAPI application
├── frontend/                        # Next.js dashboard
├── infra/
│   ├── docker-compose.yml
│   ├── nginx/nginx.conf
│   └── postgres/init.sql
└── docs/
    ├── architecture.md
    ├── event_schema.md
    ├── agent_integration.md
    └── api_spec.md
```

---

## License

MIT
