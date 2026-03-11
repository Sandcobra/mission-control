-- ---------------------------------------------------------------------------
-- Mission Control - PostgreSQL initialisation script
-- ---------------------------------------------------------------------------
-- This script runs once when the postgres container is first created.
-- Only extensions are created here — tables are created by the application
-- ORM (SQLAlchemy) on startup, and indexes are added after that.
-- ---------------------------------------------------------------------------

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";          -- uuid_generate_v4()
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements"; -- query performance monitoring
