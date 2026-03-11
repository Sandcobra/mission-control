-- ---------------------------------------------------------------------------
-- Mission Control - PostgreSQL initialisation script
-- ---------------------------------------------------------------------------
-- This script runs once when the postgres container is first created.
-- The database itself (mission_control) and the superuser (mc_user) are
-- already created by the POSTGRES_DB / POSTGRES_USER env vars before this
-- script executes.
-- ---------------------------------------------------------------------------

-- ---------------------------------------------------------------------------
-- Extensions
-- ---------------------------------------------------------------------------

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";          -- uuid_generate_v4()
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements"; -- query performance monitoring

-- ---------------------------------------------------------------------------
-- Indexes
-- These are supplementary to any indexes created by the application's ORM
-- migrations.  They are wrapped in DO blocks so re-running the script is
-- idempotent (CREATE INDEX IF NOT EXISTS is available in PG >= 9.5).
-- ---------------------------------------------------------------------------

-- agents ----------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_agents_agent_key
    ON agents (agent_key);

CREATE INDEX IF NOT EXISTS idx_agents_status
    ON agents (status);

CREATE INDEX IF NOT EXISTS idx_agents_last_heartbeat
    ON agents (last_heartbeat DESC);

-- tasks -----------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_tasks_task_key
    ON tasks (task_key);

CREATE INDEX IF NOT EXISTS idx_tasks_status
    ON tasks (status);

CREATE INDEX IF NOT EXISTS idx_tasks_assigned_agent_id
    ON tasks (assigned_agent_id);

CREATE INDEX IF NOT EXISTS idx_tasks_created_at
    ON tasks (created_at DESC);

-- Composite: common dashboard query pattern
CREATE INDEX IF NOT EXISTS idx_tasks_status_created_at
    ON tasks (status, created_at DESC);

-- task_events -----------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_task_events_task_id
    ON task_events (task_id);

CREATE INDEX IF NOT EXISTS idx_task_events_created_at
    ON task_events (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_task_events_event_type
    ON task_events (event_type);

-- Composite: fetch all events for a task ordered by time
CREATE INDEX IF NOT EXISTS idx_task_events_task_id_created_at
    ON task_events (task_id, created_at DESC);

-- agent_heartbeats ------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_agent_heartbeats_agent_id
    ON agent_heartbeats (agent_id);

CREATE INDEX IF NOT EXISTS idx_agent_heartbeats_created_at
    ON agent_heartbeats (created_at DESC);

-- Composite: fetch latest heartbeat for a specific agent
CREATE INDEX IF NOT EXISTS idx_agent_heartbeats_agent_id_created_at
    ON agent_heartbeats (agent_id, created_at DESC);

-- artifacts -------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_artifacts_task_id
    ON artifacts (task_id);

-- agent_runs ------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_agent_runs_agent_id
    ON agent_runs (agent_id);

CREATE INDEX IF NOT EXISTS idx_agent_runs_task_id
    ON agent_runs (task_id);

-- Composite: fetch all runs for an agent on a given task
CREATE INDEX IF NOT EXISTS idx_agent_runs_agent_id_task_id
    ON agent_runs (agent_id, task_id);

-- ---------------------------------------------------------------------------
-- Useful views (optional, created idempotently)
-- ---------------------------------------------------------------------------

-- Latest heartbeat per agent
CREATE OR REPLACE VIEW v_agent_latest_heartbeat AS
SELECT DISTINCT ON (agent_id)
    agent_id,
    created_at          AS heartbeat_at,
    cpu_percent,
    memory_mb,
    queue_depth
FROM agent_heartbeats
ORDER BY agent_id, created_at DESC;

-- Task summary with agent name
CREATE OR REPLACE VIEW v_task_summary AS
SELECT
    t.id,
    t.task_key,
    t.title,
    t.status,
    t.priority,
    t.created_at,
    t.updated_at,
    a.name      AS assigned_agent_name,
    a.agent_key AS assigned_agent_key
FROM tasks t
LEFT JOIN agents a ON a.id = t.assigned_agent_id;
