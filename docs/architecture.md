# Mission Control — Architecture

## System Overview

Mission Control is a real-time observability and coordination platform for
autonomous AI agents.  It provides a central hub through which multiple agents
register themselves, claim tasks, stream events, and expose cost and performance
metrics to a live dashboard.

```
                           ┌─────────────────────────────────────────────────┐
                           │                  Mission Control                 │
                           │                                                  │
  ┌──────────────┐  HTTP   │  ┌───────────┐   ┌──────────────┐              │
  │  Agent A     │ ──────► │  │  FastAPI  │   │   Next.js    │ ◄── Browser  │
  │ (OpenClaw)   │ ◄────── │  │  Backend  │   │   Frontend   │              │
  └──────────────┘  WS     │  │  :8000    │   │   :3000      │              │
                           │  └─────┬─────┘   └──────┬───────┘              │
  ┌──────────────┐  HTTP   │        │                  │                      │
  │  Agent B     │ ──────► │  ┌─────▼──────────────────▼────────────────┐   │
  │ (LangChain)  │         │  │              Nginx :80                   │   │
  └──────────────┘         │  │  /api/* → backend   / → frontend         │   │
                           │  │  /ws/*  → backend (WS upgrade)           │   │
  ┌──────────────┐  HTTP   │  └────────────────────────────────────────-─┘   │
  │  Agent C     │ ──────► │                                                  │
  │ (Custom)     │         │  ┌────────────┐     ┌─────────────┐             │
  └──────────────┘         │  │ PostgreSQL │     │    Redis     │             │
                           │  │  :5432     │     │    :6379     │             │
                           │  └────────────┘     └─────────────┘             │
                           └─────────────────────────────────────────────────┘
```

---

## Components

### Backend (FastAPI)

**Location:** `backend/`

The backend is a Python FastAPI application that:

- Exposes a REST + WebSocket API on port 8000.
- Persists all agent, task, event, and cost data to PostgreSQL via SQLAlchemy
  (async).
- Uses Redis as a pub/sub broker to fan out real-time events to all connected
  dashboard clients without polling.
- Validates inbound payloads with Pydantic v2 models.
- Authenticates agent requests via Bearer API keys stored in the database.

Key modules:

| Module | Responsibility |
|---|---|
| `routers/agents.py` | Agent registration, heartbeat, offline |
| `routers/tasks.py` | Task CRUD and assignment |
| `routers/events.py` | Ingest task events and broadcast via Redis |
| `routers/runs.py` | Agent run lifecycle and cost tracking |
| `routers/ws.py` | WebSocket endpoint for dashboard subscriptions |
| `models/` | SQLAlchemy ORM models |
| `schemas/` | Pydantic request/response schemas |
| `services/` | Business logic separated from HTTP layer |

### Frontend (Next.js)

**Location:** `frontend/`

The dashboard is a Next.js 15 application using:

- **React Server Components** for the initial data fetch on page load.
- **Client Components** with `useEffect` / `useState` for live WebSocket
  subscriptions that update agent cards and event feeds in real time.
- **Tailwind CSS** for styling.
- **shadcn/ui** for component primitives (Card, Badge, Table, etc.).

Key pages:

| Route | Purpose |
|---|---|
| `/` | Global dashboard — all agents and recent tasks |
| `/agents/[id]` | Single agent detail — heartbeat chart, active task |
| `/tasks/[id]` | Task detail — event timeline, artifacts, cost |

### Nginx

**Location:** `infra/nginx/nginx.conf`

A thin reverse proxy that:

- Terminates external HTTP on port 80.
- Routes `/api/*` and `/ws/*` to the backend.
- Routes everything else to the frontend.
- Handles the WebSocket `Upgrade` / `Connection` headers so the browser can
  open a persistent WebSocket directly through the proxy.
- Serves a `/health` probe without hitting any upstream.

### PostgreSQL

**Location:** `infra/postgres/`

PostgreSQL 16 is the primary persistent store.  All writes are transactional.
The `init.sql` script installs the `uuid-ossp` and `pg_stat_statements`
extensions and creates supporting indexes.

Schema high-level:

```
agents
  id (uuid PK), agent_key, name, runtime_type, role,
  model_provider, model_name, host, version,
  status, last_heartbeat, created_at

tasks
  id (uuid PK), task_key, title, description, status,
  priority, assigned_agent_id (FK agents),
  result_summary, error_message, metadata, created_at, updated_at

task_events
  id (uuid PK), task_id (FK tasks), agent_id (FK agents),
  event_type, message, payload (jsonb), created_at

agent_heartbeats
  id (uuid PK), agent_id (FK agents),
  cpu_percent, memory_mb, queue_depth, created_at

agent_runs
  id (uuid PK), agent_id (FK agents), task_id (FK tasks),
  token_input, token_output, estimated_cost_usd,
  started_at, ended_at

artifacts
  id (uuid PK), task_id (FK tasks), artifact_type, name,
  uri, size_bytes, metadata (jsonb), created_at
```

### Redis

Redis 7 is used exclusively as a pub/sub message broker.  When the backend
receives a task event it publishes it to a Redis channel; all backend instances
(in a scaled deployment) subscribe to that channel and push the message to
their connected WebSocket clients.

Channel naming convention:

```
mc:task:<task_id>          — events for a specific task
mc:agent:<agent_id>        — heartbeat and status changes for an agent
mc:global                  — cross-cutting broadcasts (new agent, new task)
```

---

## Data Flow

### Agent event ingestion

```
Agent process
  │
  │  POST /api/tasks/{task_id}/events
  │  Authorization: Bearer <api_key>
  │  {"event_type": "progress_updated", "payload": {"percent": 50}}
  ▼
Backend
  1. Validate API key -> resolve agent_id
  2. Validate payload with Pydantic
  3. INSERT into task_events (PostgreSQL)
  4. PUBLISH to Redis channel mc:task:<task_id>
  5. Return 201 Created with event object
  │
  │  Redis pub/sub broadcast
  ▼
All backend instances
  6. Receive message from Redis subscriber
  7. Push JSON to all WebSocket clients subscribed to task_id
  │
  │  WebSocket push
  ▼
Dashboard browsers
  8. React state update -> re-render event feed card
```

### Heartbeat flow

```
Agent (every 30s)
  POST /api/agents/heartbeat
  {"agent_id": "...", "cpu_percent": 34.2, "memory_mb": 512}
  ▼
Backend
  1. INSERT into agent_heartbeats
  2. UPDATE agents SET last_heartbeat = now(), status = 'online'
  3. PUBLISH to mc:agent:<agent_id>
  4. Return 200 OK
  ▼
Dashboard (via WebSocket)
  5. Update agent card CPU / memory sparklines
```

---

## Technology Choices

| Concern | Choice | Rationale |
|---|---|---|
| Backend language | Python 3.12 | Agent ecosystem is predominantly Python; async FastAPI gives high concurrency |
| HTTP framework | FastAPI | Native async, Pydantic integration, auto-generated OpenAPI docs |
| ORM | SQLAlchemy 2 (async) | Mature, type-safe, supports async drivers |
| Database | PostgreSQL 16 | JSONB columns for flexible payloads; strong indexing |
| Cache/pubsub | Redis 7 | Low-latency pub/sub; trivial horizontal scaling of websocket fan-out |
| Frontend | Next.js 15 + React 19 | SSR for initial load; client components for live updates |
| Styling | Tailwind CSS | Rapid, consistent styling without custom CSS |
| Proxy | Nginx | Battle-tested; minimal config for WS upgrade |
| Containerisation | Docker Compose | Zero-dependency local setup; mirrors prod topology |

---

## Scaling Considerations

### Horizontal backend scaling

Multiple backend instances can run behind a load balancer because all shared
state lives in PostgreSQL and Redis:

- Database connections are pooled per instance (SQLAlchemy `AsyncEngine` with
  `pool_size` tuned to available connections).
- WebSocket fan-out works correctly across instances because every instance
  subscribes to the same Redis channels.

### Database read replicas

Dashboard read queries (agent list, task list, event feed) can be routed to a
PostgreSQL read replica.  A `DATABASE_READONLY_URL` environment variable
switches the SQLAlchemy read-only session factory.

### Event volume

At high agent counts (hundreds of agents, thousands of events per minute):

1. Use `COPY` batching for bulk event inserts instead of single-row INSERTs.
2. Partition `task_events` and `agent_heartbeats` by `created_at` (monthly) so
   old partitions can be detached and archived without locking.
3. Route high-frequency heartbeat writes through a Redis time-series buffer
   and flush to Postgres on a 10-second cadence.

### Frontend

The Next.js frontend is stateless and can be scaled horizontally behind the
same Nginx layer.  Static assets are cached at the CDN layer when deployed to
production (Vercel, Cloudflare, etc.).
