# Mission Control — API Specification

Base URL: `http://localhost:8000` (or your deployed URL)

All endpoints under `/api/` require a Bearer API key unless noted otherwise.

---

## Authentication

Pass the API key as a Bearer token in the `Authorization` header:

```
Authorization: Bearer <api-key>
```

API keys are pre-provisioned by an administrator.  On first use the key is
resolved to an agent record (or used as a service key for read-only operations).

---

## Error Response Format

All 4xx and 5xx responses return a consistent JSON body:

```json
{
  "detail": "Human-readable error description.",
  "code":   "MACHINE_READABLE_CODE",
  "field":  "field_name_if_validation_error"
}
```

Common error codes:

| HTTP | Code | Meaning |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Request body failed schema validation |
| 401 | `UNAUTHORIZED` | Missing or invalid API key |
| 403 | `FORBIDDEN` | Key exists but lacks permission for this operation |
| 404 | `NOT_FOUND` | Requested resource does not exist |
| 409 | `CONFLICT` | Duplicate `agent_key` or `task_key` |
| 422 | `UNPROCESSABLE` | Semantically invalid input |
| 500 | `INTERNAL_ERROR` | Unexpected server error |

---

## Ingest Endpoints

### POST /api/agents/register

Register a new agent or update an existing one (upsert on `agent_key`).

**Request**

```json
{
  "agent_key":      "my-agent-01",
  "name":           "My Research Agent",
  "runtime_type":   "custom",
  "role":           "researcher",
  "model_provider": "anthropic",
  "model_name":     "claude-sonnet-4-6",
  "host":           "worker-01.internal",
  "version":        "1.0.0"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `agent_key` | string | yes | Stable external identifier; upsert key |
| `name` | string | yes | Human-readable display name |
| `runtime_type` | string | yes | Runtime category tag |
| `role` | string | yes | Functional role tag |
| `model_provider` | string | yes | LLM provider |
| `model_name` | string | yes | LLM model identifier |
| `host` | string | no | Hostname; defaults to request IP |
| `version` | string | no | Agent code version |

**Response 201 Created**

```json
{
  "id":             "550e8400-e29b-41d4-a716-446655440000",
  "agent_key":      "my-agent-01",
  "name":           "My Research Agent",
  "runtime_type":   "custom",
  "role":           "researcher",
  "model_provider": "anthropic",
  "model_name":     "claude-sonnet-4-6",
  "host":           "worker-01.internal",
  "version":        "1.0.0",
  "status":         "online",
  "last_heartbeat": "2026-03-11T12:00:00Z",
  "created_at":     "2026-03-11T12:00:00Z"
}
```

---

### POST /api/agents/heartbeat

Report liveness and optional resource metrics.

**Request**

```json
{
  "agent_id":    "550e8400-e29b-41d4-a716-446655440000",
  "agent_key":   "my-agent-01",
  "cpu_percent": 34.2,
  "memory_mb":   512.0,
  "queue_depth": 2
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `agent_id` | UUID | yes* | Agent UUID from registration |
| `agent_key` | string | yes* | At least one of `agent_id` or `agent_key` required |
| `cpu_percent` | float | no | 0-100 CPU utilisation |
| `memory_mb` | float | no | Resident memory in MB |
| `queue_depth` | integer | no | Pending tasks in agent's local queue |

**Response 200 OK**

```json
{
  "status": "ok",
  "server_time": "2026-03-11T12:00:30Z"
}
```

---

### POST /api/agents/offline

Mark an agent as offline.

**Request**

```json
{
  "agent_id":  "550e8400-e29b-41d4-a716-446655440000",
  "agent_key": "my-agent-01"
}
```

**Response 200 OK**

```json
{ "status": "ok" }
```

---

### POST /api/tasks

Create a new task.

**Request**

```json
{
  "task_key":    "nba-research-2026-03-11",
  "title":       "Research NBA Slate 2026-03-11",
  "description": "Fetch game schedule and odds.",
  "priority":    7,
  "metadata": {
    "league": "NBA",
    "date":   "2026-03-11"
  }
}
```

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `task_key` | string | yes | — | Stable external identifier |
| `title` | string | yes | — | Short human-readable title |
| `description` | string | no | null | Longer description |
| `priority` | integer | no | 5 | 1 (lowest) to 10 (highest) |
| `metadata` | object | no | `{}` | Arbitrary key/value pairs |

**Response 201 Created** — returns the task object (see GET /api/tasks/{id}).

---

### POST /api/tasks/{task_id}/assign

Assign a task to an agent.

**Path Parameters**

| Name | Type | Description |
|---|---|---|
| `task_id` | UUID | Task to assign |

**Request**

```json
{
  "agent_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response 200 OK** — returns the updated task object.

---

### POST /api/tasks/{task_id}/events

Emit a task lifecycle event.

**Request**

```json
{
  "event_type": "progress_updated",
  "agent_id":   "550e8400-e29b-41d4-a716-446655440000",
  "message":    "Fetching NBA odds",
  "payload": {
    "percent":      45,
    "current_step": "fetch_odds"
  }
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `event_type` | string | yes | See event schema docs |
| `agent_id` | UUID | yes | Emitting agent |
| `message` | string | no | Human-readable summary |
| `payload` | object | no | Event-specific structured data |

**Response 201 Created**

```json
{
  "id":         "uuid",
  "task_id":    "uuid",
  "agent_id":   "uuid",
  "event_type": "progress_updated",
  "message":    "Fetching NBA odds",
  "payload":    { "percent": 45, "current_step": "fetch_odds" },
  "created_at": "2026-03-11T12:01:00Z"
}
```

---

### PATCH /api/tasks/{task_id}

Update task fields (typically status transitions).

**Request** (all fields optional)

```json
{
  "status":         "completed",
  "result_summary": "Generated 4 betting lines.",
  "error_message":  null
}
```

**Response 200 OK** — returns the updated task object.

---

### POST /api/tasks/{task_id}/artifacts

Register an artifact associated with a task.

**Request**

```json
{
  "artifact_type": "csv",
  "name":          "nba_slate_2026-03-11.csv",
  "uri":           "s3://my-bucket/outputs/nba_slate_2026-03-11.csv",
  "size_bytes":    4096,
  "metadata": {
    "row_count": 48
  }
}
```

**Response 201 Created**

```json
{
  "id":            "uuid",
  "task_id":       "uuid",
  "artifact_type": "csv",
  "name":          "nba_slate_2026-03-11.csv",
  "uri":           "s3://my-bucket/outputs/nba_slate_2026-03-11.csv",
  "size_bytes":    4096,
  "metadata":      { "row_count": 48 },
  "created_at":    "2026-03-11T12:02:00Z"
}
```

---

### POST /api/runs

Create a new agent run record.

**Request**

```json
{
  "agent_id": "uuid",
  "task_id":  "uuid"
}
```

**Response 201 Created**

```json
{
  "id":         "uuid",
  "agent_id":   "uuid",
  "task_id":    "uuid",
  "started_at": "2026-03-11T12:00:00Z"
}
```

---

### POST /api/runs/{run_id}/cost

Record token usage and estimated cost for a run.

**Request**

```json
{
  "token_input":          1200,
  "token_output":         450,
  "estimated_cost_usd":   0.0037
}
```

**Response 200 OK**

```json
{
  "id":                   "uuid",
  "agent_id":             "uuid",
  "task_id":              "uuid",
  "token_input":          1200,
  "token_output":         450,
  "estimated_cost_usd":   0.0037,
  "updated_at":           "2026-03-11T12:05:00Z"
}
```

---

## Read Endpoints

### GET /api/agents

List all agents.

**Query Parameters**

| Name | Type | Default | Description |
|---|---|---|---|
| `status` | string | — | Filter by status: `online`, `offline` |
| `role` | string | — | Filter by role |
| `limit` | integer | 50 | Max results (1-200) |
| `offset` | integer | 0 | Pagination offset |

**Response 200 OK**

```json
{
  "items": [
    {
      "id":             "uuid",
      "agent_key":      "my-agent-01",
      "name":           "My Research Agent",
      "status":         "online",
      "role":           "researcher",
      "model_name":     "claude-sonnet-4-6",
      "last_heartbeat": "2026-03-11T12:00:30Z",
      "created_at":     "2026-03-11T10:00:00Z"
    }
  ],
  "total":  1,
  "limit":  50,
  "offset": 0
}
```

---

### GET /api/agents/{agent_id}

Fetch a single agent by UUID.

**Response 200 OK** — full agent object including latest heartbeat metrics.

---

### GET /api/tasks

List tasks.

**Query Parameters**

| Name | Type | Default | Description |
|---|---|---|---|
| `status` | string | — | Filter: `pending`, `assigned`, `running`, `completed`, `failed`, `blocked` |
| `assigned_agent_id` | UUID | — | Filter by agent |
| `priority_gte` | integer | — | Minimum priority |
| `limit` | integer | 50 | Max results (1-200) |
| `offset` | integer | 0 | Pagination offset |
| `order` | string | `created_at_desc` | Sort order |

**Response 200 OK**

```json
{
  "items": [
    {
      "id":                  "uuid",
      "task_key":            "nba-research-2026-03-11",
      "title":               "Research NBA Slate",
      "status":              "running",
      "priority":            7,
      "assigned_agent_name": "My Research Agent",
      "created_at":          "2026-03-11T12:00:00Z",
      "updated_at":          "2026-03-11T12:01:00Z"
    }
  ],
  "total":  1,
  "limit":  50,
  "offset": 0
}
```

---

### GET /api/tasks/{task_id}

Fetch a single task.

**Response 200 OK** — full task object.

---

### GET /api/tasks/{task_id}/events

Fetch the event timeline for a task.

**Query Parameters**

| Name | Type | Default | Description |
|---|---|---|---|
| `event_type` | string | — | Filter by type |
| `limit` | integer | 100 | Max results |
| `offset` | integer | 0 | Pagination offset |

**Response 200 OK**

```json
{
  "items": [
    {
      "id":         "uuid",
      "event_type": "progress_updated",
      "message":    "Fetching odds",
      "payload":    { "percent": 50 },
      "created_at": "2026-03-11T12:01:00Z"
    }
  ],
  "total": 1
}
```

---

### GET /api/tasks/{task_id}/artifacts

List artifacts for a task.

**Response 200 OK** — array of artifact objects.

---

### GET /api/runs/{run_id}

Fetch a single run with its cost data.

**Response 200 OK**

```json
{
  "id":                 "uuid",
  "agent_id":           "uuid",
  "task_id":            "uuid",
  "token_input":        1200,
  "token_output":       450,
  "estimated_cost_usd": 0.0037,
  "started_at":         "2026-03-11T12:00:00Z",
  "ended_at":           null
}
```

---

### GET /health

Health probe — does not require authentication.

**Response 200 OK**

```json
{
  "status": "ok",
  "version": "1.0.0",
  "db": "ok",
  "redis": "ok"
}
```

---

## WebSocket Channels

Connect to the WebSocket endpoint:

```
ws://localhost:8000/ws?token=<api-key>
```

### Subscribe

After connecting, send a subscribe message:

```json
{
  "action": "subscribe",
  "channel": "task",
  "id": "<task_id>"
}
```

```json
{
  "action": "subscribe",
  "channel": "agent",
  "id": "<agent_id>"
}
```

```json
{
  "action": "subscribe",
  "channel": "global"
}
```

### Unsubscribe

```json
{
  "action": "unsubscribe",
  "channel": "task",
  "id": "<task_id>"
}
```

### Inbound Message Format

All messages pushed by the server follow this envelope:

```json
{
  "channel":  "task",
  "id":       "<task_id>",
  "event":    "task_event",
  "payload":  {
    "id":         "uuid",
    "task_id":    "uuid",
    "agent_id":   "uuid",
    "event_type": "progress_updated",
    "message":    "Fetching odds",
    "payload":    { "percent": 50 },
    "created_at": "2026-03-11T12:01:00Z"
  }
}
```

### Event Types on the `global` Channel

| `event` field | Description |
|---|---|
| `agent_registered` | New agent registered |
| `agent_status_changed` | Agent went online or offline |
| `task_created` | New task was created |
| `task_status_changed` | Task status transition |

### Error Message

If a subscribe message is malformed:

```json
{
  "channel": "error",
  "event":   "invalid_message",
  "payload": { "detail": "Missing required field: id" }
}
```
