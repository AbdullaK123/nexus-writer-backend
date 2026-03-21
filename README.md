# Nexus Writer Backend

FastAPI-based backend API for the Nexus Writer application. It provides user, story, chapter, target, and analytics endpoints, AI-powered manuscript analysis (plot, character, structure, world-building), Prefect-orchestrated extraction workflows, and a Socket.IO ASGI app for realtime features.

This README documents the tech stack, requirements, environment variables, setup instructions, run commands, scripts, migrations, testing, project structure, and licensing notes.

## Overview
- Framework: FastAPI (ASGI)
- Realtime: python-socketio (ASGIApp wrapper around FastAPI)
- Data access: SQLModel (on top of SQLAlchemy Async), asyncpg (PostgreSQL)
- Document store: MongoDB (AI extractions — plot, character, structure, world)
- Migrations: Alembic
- Caching/queues: Redis (redis[hiredis])
- Workflow orchestration: Prefect (extraction flows, line-edit flows)
- AI / LLM: Google Gemini (langchain-google-genai), OpenAI
- Analytics: DuckDB / MotherDuck (see motherduck_url), with pandas/numpy for metrics
- Cloud integrations: AWS S3 via boto3 (mypy-boto3-s3 types)
- Logging: loguru

Entry point: main.py defines a FastAPI app and exports `socket_app`, which is the Socket.IO ASGI application to run under Uvicorn or another ASGI server.

## Requirements
- Python 3.10 or newer
- Package manager: uv (recommended) — uv.lock is present
  - Install uv: https://docs.astral.sh/uv/
- Docker (for running the local PostgreSQL dev database via the provided script)
- Redis (local or remote). You can use Docker or a managed Redis instance.

Optional but useful:
- make (if you plan to add Makefile wrappers) — not provided in this repo

## Environment variables
Configuration is managed via pydantic-settings (app/config/settings.py). Create a .env file in the project root with the following keys:

Required:
- motherduck_url: Analytics data warehouse connection string (DuckDB/MotherDuck)
- database_url: Async SQLAlchemy connection string for the app DB
  - Example: postgresql+asyncpg://USER:PASS@HOST:5432/DBNAME
- database_sync_url: Sync SQLAlchemy connection string for the app DB
- migration_url: Sync SQLAlchemy connection string for Alembic migrations
  - Example: postgresql://USER:PASS@HOST:5432/DBNAME
- mongodb_url: MongoDB connection string for AI extraction data
  - Example: mongodb://localhost:27017/nexus_writer
- app_secret_key: Secret key for password hashing
- cookie_signing_key: Key for verifying the signature of encrypted session ids
- cookie_encryption_key: Key for encrypting cookies
- redis_url: Redis connection URI
  - Example: redis://localhost:6379/0
- redis_broker_url: Redis broker URI (for task queues)
- openai_api_key: OpenAI API key
- gemini_api_key: Google Gemini API key
- ai_temperature: LLM temperature for structured outputs
- ai_maxtokens: Max tokens for LLM structured outputs

Optional:
- env: Runtime environment label (default: dev)
- debug: Enable verbose logging/SQL echo (bool, default: false)
- password_pattern: Regex for password complexity (default present in code)
- prefect_api_url: Prefect server API URL (required when running with Prefect orchestration)
- default_task_retries: Prefect task retry count (default: 1)
- default_task_retry_delay: Retry delay in seconds (default: 10)
- extraction_task_timeout: Per-task timeout for extraction in seconds (default: 120)
- chapter_flow_timeout: Chapter extraction flow timeout in seconds (default: 180)
- result_storage_ttl: Prefect result storage TTL in seconds (default: 86400)
- ai_sdk_timeout: HTTP timeout per LLM request in seconds (default: 90)
- ai_sdk_retries: SDK-level retries for transient LLM errors (default: 2)

Tip: See app/config/settings.py for authoritative field descriptions and defaults.

## Setup
Using uv (recommended):
1) Ensure you have uv installed.
2) From the repo root, create your virtual environment and install dependencies:
   - uv sync
3) Create a .env file as described above.

Alternative without uv (not recommended):
- There is no requirements.txt in this repo. You can either:
  - Use pip to manually install the packages listed under [project.dependencies] in pyproject.toml, or
  - Generate a requirements.txt (TODO: add a pinned requirements.txt for pip users).

## Running the application
Development (auto-reload):
- uv run uvicorn main:socket_app --reload --host 0.0.0.0 --port 8000

Production (basic example):
- uv run uvicorn main:socket_app --host 0.0.0.0 --port 8000 --workers 4

Health check:
- GET http://localhost:8000/health should return a simple JSON message.

CORS:
- CORS is set to allow all origins by default in main.py. Review before production.

## Database and migrations
Alembic is configured via alembic.ini and migrations/env.py. It loads the `migration_url` from your .env.

Common commands:
- Apply latest migrations: alembic upgrade head
- Create a new migration: alembic revision -m "short message" --autogenerate
- Downgrade one step: alembic downgrade -1

Note: Ensure `migration_url` points to a synchronous SQLAlchemy URI (e.g., postgresql://...), not the async driver.

### Dev database helper script
The repo includes a helper script to bootstrap a local PostgreSQL 17 with pgvector using Docker and then run migrations.

- scripts/init_dev_db.sh
  - Kills any processes using port 5432 (Linux tools), removes existing containers binding 5432, starts a pgvector/pgvector:pg17 container, waits for readiness, runs alembic upgrade head, and prints a usable connection string.
  - Usage (Linux/macOS/WSL):
    - bash scripts/init_dev_db.sh
  - After it completes, you can set:
    - database_url=postgresql+asyncpg://nexus_user:password@localhost:5432/nexus_writer
    - migration_url=postgresql://nexus_user:password@localhost:5432/nexus_writer

## Redis
The app expects redis_url in your .env. You can run Redis in Docker for dev:
- docker run -d --name redis -p 6379:6379 redis:7
- Then set redis_url=redis://localhost:6379/0

## Running with Docker Compose

The application can be run with Docker Compose, which includes:

- **postgres-nexus**: Main application database (PostgreSQL 17)
- **postgres-prefect**: Prefect server database (PostgreSQL 17)
- **redis-nexus**: Redis for caching
- **prefect-server**: Prefect orchestration server (UI at http://localhost:4200)
- **prefect-worker**: Dedicated container for running Prefect workflows
- **nexus-writer**: Main FastAPI API server

### Starting the services

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f prefect-worker
docker-compose logs -f nexus-writer

# Stop all services
docker-compose down
```

### Architecture

The Prefect workflows run in a **separate container** from the API server:

1. **API Server (nexus-writer)**: Handles HTTP requests and submits flow runs to Prefect
2. **Prefect Server**: Orchestrates and schedules flow runs, provides UI dashboard
3. **Prefect Worker**: Executes the actual flow code for extraction and line edits

When a job is queued via the API:
1. The API submits a flow run to the Prefect server via `run_deployment()`
2. The Prefect server schedules the run
3. The worker picks up the run and executes it
4. Job status can be polled via the API

### Prefect UI

Access the Prefect dashboard at http://localhost:4200 to:
- View flow runs and their status
- Monitor worker health
- See flow run logs and results
- Manage deployments

### Scaling workers

To scale the number of workers:

```bash
docker-compose up -d --scale prefect-worker=3
```

## Scripts
- scripts/init_dev_db.sh — Initialize local PostgreSQL with pgvector and run migrations
- scripts/reset_db.sh — Reset the database by downgrading to base and upgrading to head (DROPS ALL DATA). Usage: `bash scripts/reset_db.sh [--yes]`

If additional scripts are added under scripts/, document them here. TODO: list and describe other helper scripts if/when they are introduced.

## Tests
This repo uses JetBrains HTTP Client / VSCode REST Client style suites under test/ to exercise the API end-to-end. Start the server and run the requests from top to bottom; cookies (session_id) are preserved between requests for localhost.

HTTP suites:
- test_auth.http — registration, login, /auth/me, logout, negative cases (dup email 409, invalid email 422, wrong password 401), X-Request-ID checks.
- test_story_crud.http — create/list/details/update/status, duplicate title negative, cross-user access negatives (403), non-existent story (404), delete and duplicate delete (404).
- test_chapter_crud.http — create multiple chapters, list, get with navigation, update, reorder, delete; non-existent chapter GET/PUT/DELETE (404); X-Request-ID check.
- test_target_crud.http — comprehensive target flows across frequencies, duplicates (409), invalid ranges (422), invalid enum (422), cross-user (403), idempotent deletes, timezone normalization checks, header check.
- test_analytics.http — analytics defaults and explicit ranges/frequencies, invalid frequency (422), header check; cleanup.
- test_e2e.http — full scenario chaining auth → story → chapters → targets → analytics → cleanup.
- test_unauthenticated.http — verifies protected endpoints return 403 without a session.

How to run:
1) Start server: uv run uvicorn main:socket_app --reload --host 0.0.0.0 --port 8000
2) Open any .http file under test/ and execute requests sequentially.
3) Inspect logs/http.log for structured request logs with correlation IDs (X-Request-ID).

Optional pytest
- You can still add pytest-based tests under a tests/ directory and run with: uv run pytest -q

## Project structure (high-level)
- main.py — FastAPI app + Socket.IO ASGI wrapper (socket_app)
- worker.py — Prefect worker entry point (serves extraction & line-edit flow deployments)
- app/
  - controllers/ — API routers
    - auth.py — Registration, login, sessions, logout
    - chapter.py — Chapter CRUD and operations
    - jobs.py — Job status and management
    - story.py — Story CRUD, includes sub-routers for nested resources
    - story_characters.py — Character extraction endpoints + tracker (presence map, introduction rate, density, goals, knowledge map, cast report)
    - story_plot.py — Plot extraction endpoints + tracker (threads, dormant threads, event density, setup-payoff map, density, rhythm report)
    - story_structure.py — Structure and pacing endpoints
    - story_targets.py — Writing target endpoints
    - story_world.py — World-building endpoints
  - services/ — Business logic and integration layers
    - analytics.py — MotherDuck analytics queries
    - auth.py — Authentication logic
    - chapter.py — Chapter operations
    - character.py — Character extraction service (arc, knowledge, inconsistency report)
    - character_tracker.py — Character tracker service (presence map, introduction rate, goals, knowledge asymmetry, cast density, cast management report)
    - jobs.py — Job orchestration
    - plot.py — Plot extraction service (threads, questions, setups, contrivances, structural report)
    - plot_tracker.py — Plot tracker service (thread timeline, dormant threads, event density, setup-payoff map, plot density, rhythm report)
    - story.py — Story CRUD operations
    - structure.py — Structure service (pacing, structural arc, weak scenes, emotional beats, developmental report)
    - target.py — Writing target service
    - world.py — World-building service (facts, contradictions, consistency report)
  - ai/ — AI / LLM integration layer
    - Top-level modules invoke LLMs and parse structured output: character.py, character_bio.py, context.py, edits.py, plot.py, plot_thread.py, structure.py, structure_and_pacing.py, timeline.py, world.py, world_bible.py
    - models/ — Pydantic schemas for structured LLM output (one per domain)
    - prompts/ — System and human prompt templates (one per domain)
  - schemas/ — Pydantic models for API requests/responses (story, chapter, analytics, target, character, plot, structure, world, jobs)
  - models/ — SQLModel models and enums
  - core/ — Infrastructure (database engine, MongoDB client, Redis client, security)
  - config/ — Settings, logging, Prefect config, application lifespan
  - flows/ — Prefect workflows
    - extraction/ — Chapter extraction flow, re-extraction flow, shared tasks
    - line_edits/ — Line-edit suggestion flow
  - jobs/ — Job dispatching (chapter, session)
  - workers/ — Worker base abstraction
  - utils/ — Utility modules (AI helpers, decorators, HTML/Lexical parsing, logging context)
  - channels/ — Socket.IO server setup (analytics channel)
  - middleware/ — HTTP logging middleware
- migrations/ — Alembic migration environment and versions
- scripts/ — Helper scripts (dev DB bootstrap, DB reset)
- pyproject.toml — Project metadata and dependencies
- uv.lock — uv lockfile with pinned dependency resolutions
- alembic.ini — Alembic configuration
- logs/ — Log files (if used)

Note: Actual submodules may evolve. Explore the app/ package for details.

## API surface (example)
- Stories: CRUD, chapters, reordering, analytics (frequency, date range), and writing targets
- Health: GET /health

For the full API, inspect the controllers in app/controllers/ and run the app to view generated OpenAPI docs at /docs.

## License
No explicit license file is present. TODO: Add a LICENSE file (e.g., MIT, Apache-2.0) and update this section accordingly.


## HTTP request/response logging
The application now includes comprehensive, structured logging for all HTTP flows via a Loguru-powered middleware.

- Location: logs/http.log (rotates at 50 MB, retention 30 days, JSON-serialized entries)
- Console: Summarized request lines are also printed to stdout.
- Fields captured per request:
  - correlation_id (also returned to clients as X-Request-ID)
  - method, path, query (with sensitive params redacted)
  - status, duration_ms
  - client_ip (X-Real-IP if provided, else socket peer), user_agent
  - session_present (boolean), user_id (when authenticated)
  - response_length (when available)
- Privacy & safety:
  - Sensitive endpoints (/auth/login, /auth/register) are marked and bodies are not logged. Query string is lightly redacted for password-like keys.

You can correlate client-side telemetry with server logs using the X-Request-ID response header.


## Bullet-proof logging and diagnostics
The application includes end-to-end, correlation-aware logging designed to be safe and actionable in production.

What you get:
- Correlation IDs on all requests (X-Request-ID header) and in all HTTP logs. Correlation ID is propagated to downstream logs inside services using a request-scoped context.
- Structured JSON logs for HTTP, DB operations, retries, performance, and errors, with rotation and retention configured under logs/.
- Global exception handler captures and logs unexpected errors and returns a 500 JSON body including the correlation_id for easy support triage.
- Sensitive paths are tagged (no request/response bodies are logged; query string has narrow redaction of password-like keys).

Where to look:
- logs/http.log — structured HTTP request summaries with status, latency, client, and correlation_id.
- logs/database.log — application-level DB-operation logs (create/update/delete/list for targets; auth session/user events) enriched with correlation_id and user_id when available.
- logs/errors.log — stack traces and error entries.
- logs/performance.log, logs/retry_attempts.log, logs/background_jobs.log — specialized channels.

Implementation notes:
- Context propagation uses contextvars to carry correlation_id and user_id. See app/utils/logging_context.py.
- HTTP middleware (app/middleware/http_logging.py) sets/clears context per-request and emits structured logs.
- Services use context-aware logging to ensure domain events are always tied back to the request.
- main.py registers a global exception handler that logs with the current correlation context.

Operational guidance:
- When reporting issues, always include the X-Request-ID returned by the API; it can be searched across all logs.
- For local debugging, tail -f logs/http.log and logs/errors.log while running the HTTP suites under test/.
