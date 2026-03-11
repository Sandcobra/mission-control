# Mission Control — Event Schema

All task lifecycle and observability information flows through the event system.
Events are stored in `task_events` and broadcast in real time via WebSocket.

---

## Event Object Structure

Every event object has the following top-level shape:

```json
{
  "id":         "uuid",
  "task_id":    "uuid",
  "agent_id":   "uuid",
  "event_type": "string",
  "message":    "string | null",
  "payload":    { },
  "created_at": "ISO-8601 timestamp"
}
```

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Unique event identifier |
| `task_id` | UUID | The task this event belongs to |
| `agent_id` | UUID | The agent that emitted this event |
| `event_type` | string | One of the well-known types listed below |
| `message` | string or null | Human-readable summary; shown in the dashboard timeline |
| `payload` | object | Event-specific structured data (schema varies by type) |
| `created_at` | ISO-8601 | Server-side timestamp |

---

## Well-Known Event Types

### task_started

Emitted when an agent begins executing a task.

```json
{
  "event_type": "task_started",
  "message": "Task execution has begun.",
  "payload": {}
}
```

**Effect:** Transitions task `status` → `running`.

---

### progress_updated

Reports incremental progress.  Drives the progress bar in the dashboard.

```json
{
  "event_type": "progress_updated",
  "message": "Fetching NBA odds",
  "payload": {
    "percent": 45,
    "current_step": "fetch_odds"
  }
}
```

| Payload field | Type | Required | Description |
|---|---|---|---|
| `percent` | integer 0-100 | yes | Completion percentage |
| `current_step` | string | no | Label for the active processing step |

---

### tool_called

Emitted immediately before an agent invokes a tool (web search, API call, etc.).

```json
{
  "event_type": "tool_called",
  "message": "Calling tool: fetch_odds",
  "payload": {
    "tool_name": "fetch_odds",
    "args": {
      "game_id": "g-001",
      "markets": ["h2h", "spreads"]
    }
  }
}
```

| Payload field | Type | Required | Description |
|---|---|---|---|
| `tool_name` | string | yes | Canonical tool identifier |
| `args` | object | no | Serialised call arguments |

---

### tool_result_received

Emitted after an agent receives a tool result.

```json
{
  "event_type": "tool_result_received",
  "message": "Tool result received from fetch_odds",
  "payload": {
    "tool_name": "fetch_odds"
  }
}
```

| Payload field | Type | Required | Description |
|---|---|---|---|
| `tool_name` | string | yes | Canonical tool identifier |

---

### task_completed

Emitted when a task finishes successfully.

```json
{
  "event_type": "task_completed",
  "message": "Research complete.  Generated 4 betting lines.",
  "payload": {
    "result_summary": "Research complete.  Generated 4 betting lines."
  }
}
```

**Effect:** Transitions task `status` → `completed`.

---

### task_failed

Emitted when a task encounters an unrecoverable error.

```json
{
  "event_type": "task_failed",
  "message": "Odds API returned 429 after 3 retries.",
  "payload": {
    "error_message": "Odds API returned 429 after 3 retries.",
    "error_type": "RateLimitError",
    "retryable": true
  }
}
```

| Payload field | Type | Required | Description |
|---|---|---|---|
| `error_message` | string | yes | Full error description |
| `error_type` | string | no | Python exception class or custom category |
| `retryable` | boolean | no | Whether the orchestrator should re-queue the task |

**Effect:** Transitions task `status` → `failed`.

---

### task_blocked

Emitted when a task cannot continue until external input is provided.

```json
{
  "event_type": "task_blocked",
  "message": "Awaiting human approval before placing wager.",
  "payload": {
    "reason": "Awaiting human approval before placing wager."
  }
}
```

**Effect:** Transitions task `status` → `blocked`.

---

### log_output

General-purpose log lines captured from agent stdout.

```json
{
  "event_type": "log_output",
  "message": "Loaded 12 games from schedule API",
  "payload": {
    "lines": [
      "Loaded 12 games from schedule API",
      "Processing game g-001 (Lakers vs Celtics)"
    ]
  }
}
```

---

### Custom Event Types

Agents may emit any custom `event_type` string.  Custom events are stored and
broadcast exactly like well-known events; they appear in the event timeline
under their type label.  The convention is `snake_case`.

---

## Channel Routing Table

Events are broadcast on Redis pub/sub channels and forwarded to WebSocket
clients based on the subscriptions they registered at connect time.

| Redis Channel | Published On | Subscribed By |
|---|---|---|
| `mc:task:<task_id>` | Every task event | Dashboard task detail page |
| `mc:agent:<agent_id>` | Heartbeat, status change, task assignment | Dashboard agent detail page |
| `mc:global` | New agent registered, new task created | Dashboard home page |

---

## Task Lifecycle State Machine

```
                   ┌─────────┐
         create    │         │
        ──────────►│ pending │
                   │         │
                   └────┬────┘
                        │ assign
                        ▼
                   ┌─────────┐
                   │assigned │
                   └────┬────┘
                        │ task_started
                        ▼
              ┌─────────────────┐
        ┌────►│    running      │◄────┐
        │     └───┬──────┬──────┘     │
        │         │      │             │ (unblock)
        │ (retry) │      │ task_blocked│
        │         │      ▼             │
        │         │  ┌────────┐        │
        │         │  │blocked │────────┘
        │         │  └────────┘
        │         │
        │    task_completed     task_failed
        │         │                   │
        │         ▼                   ▼
        │   ┌──────────┐       ┌──────────┐
        └───│ completed│       │  failed  │
            └──────────┘       └──────────┘
```

---

## Event Lifecycle in a Typical Task

```
Time │  Event Type           │  Notes
─────┼───────────────────────┼──────────────────────────────────────
  0s │  task_started         │  Agent picks up the task
  2s │  progress_updated     │  percent=10, step="init"
  5s │  tool_called          │  tool_name="fetch_schedule"
  6s │  tool_result_received │  tool_name="fetch_schedule"
  6s │  progress_updated     │  percent=25, step="schedule_loaded"
  7s │  tool_called          │  tool_name="fetch_odds" (game 1)
  8s │  tool_result_received │  tool_name="fetch_odds"
 ...
 30s │  progress_updated     │  percent=80, step="model_inference"
 35s │  tool_called          │  tool_name="write_report"
 36s │  tool_result_received │  tool_name="write_report"
 36s │  progress_updated     │  percent=100, step="done"
 36s │  task_completed       │  result_summary="..."
```
