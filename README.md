# Nexus Writer Backend

Backend for **Nexus Writer**, a story-writing application built around a rich editor, structured story data, background analysis, semantic retrieval, and a grounded AI story assistant.

The frontend lives in a separate repository: [AbdullaK123/nexus-writer-frontend-spa](https://github.com/AbdullaK123/nexus-writer-frontend-spa).

## What this backend does

Nexus Writer is not a simple CRUD API. The backend coordinates mutable story state across browser requests, PostgreSQL, Redis, background workers, and AI providers while preserving correctness under retries and concurrency.

Core capabilities include:

- user registration, password login, Google OAuth, cookie-backed sessions, settings, and per-user navigation/dashboard data
- story and chapter creation, editing, deletion, publishing, and ordered chapter hierarchies
- background scene extraction, embeddings, comments, summaries, and derived story analysis
- hybrid scene search using PostgreSQL full-text search and pgvector embeddings
- persisted, story-scoped AI chat threads streamed over Server-Sent Events
- tool-using story research grounded in chapters, scenes, metadata, and internal analytics
- Redis-backed notifications and background-job coordination
- scheduled maintenance and processing via a cron worker

## Architecture

The backend uses explicit layers rather than an ORM-centric active-record model:

```text
HTTP request
    |
    v
FastAPI controller
    |
    v
Service layer
    |
    +--> repositories --> PostgreSQL
    +--> Redis / queues
    +--> AI providers
    +--> SSE / notifications
```

The main source tree is:

```text
.
├── main.py                 # FastAPI entry point
├── saq_worker.py           # Redis/SAQ background worker
├── cron_worker.py          # scheduled jobs
├── src/
│   ├── app/                # controllers, dependencies, middleware, lifespan
│   ├── data/               # raw asyncpg repositories + schemas
│   ├── infrastructure/     # config, auth, Redis, AI providers, telemetry
│   ├── service/            # application/domain orchestration
│   └── shared/             # shared utilities and text types
├── migrations/yoyo/        # PostgreSQL migrations
├── tests/                  # app, service, data, infrastructure, worker tests
├── evals/                  # AI behavior/evaluation harnesses
├── dev_scripts/            # local development helpers
├── docker-compose.yml
└── Makefile
```

### State and concurrency model

PostgreSQL is the canonical source of truth. Redis, queued jobs, caches, and AI outputs are derived or transient state.

Write paths are deliberately designed so timing does not decide correctness. Depending on the resource, the codebase uses:

- atomic SQL mutations and database constraints
- short transactions and row-level locking
- PostgreSQL advisory locks for logical resources that may not have a row yet
- serialized mutation boundaries for ordering-sensitive operations
- idempotency and stale-state checks for background work
- explicit separation between canonical DB commits and derived side effects

OAuth account creation/linking is also concurrency-controlled: callbacks serialize on canonical provider identity and normalized email before reading and creating account state.

## Tech stack

- **Python** 3.12 in Docker (`pyproject.toml` declares Python 3.10+)
- **FastAPI** + Uvicorn
- **PostgreSQL 18** via `pgvector/pgvector:pg18`
- **asyncpg** for application queries
- **yoyo-migrations** for schema migrations
- **Redis** for sessions/coordination/pub-sub support
- **SAQ** for background jobs
- **OpenAI / OpenRouter** for model access
- **Pydantic AI** + `pydantic-ai-harness` for the story agent/evals
- **Loguru**, Logfire, and OpenTelemetry instrumentation
- **pytest**, `pytest-asyncio`, and Testcontainers for testing

## Configuration

Create a `.env` file in the repository root.

Required environment variables:

```env
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
APP_SECRET_KEY=replace-with-at-least-32-characters

OPENAI_API_KEY=...
OPEN_ROUTER_API_KEY=...
OPEN_ROUTER_API_URL=...

CLIENT_ID=...          # Google OAuth client ID
CLIENT_SECRET=...      # Google OAuth client secret
SESSION_SECRET=...
```

Useful optional settings include:

```env
ENV=dev                # dev | staging | prod
DEBUG=false
CORS_ORIGINS=["http://localhost:5173"]
```

Static application tuning lives in `src/infrastructure/config/config.yaml`; deployment-specific secrets and environment values are loaded through `pydantic-settings` in `src/infrastructure/config/settings.py`.

## Run with Docker Compose

The easiest way to run the complete backend stack is:

```bash
docker compose up --build
```

Services:

- `postgres-nexus` — PostgreSQL + pgvector
- `nexus-redis` — Redis
- `nexus-writer` — FastAPI API
- `saq-worker` — queued background jobs
- `cron-worker` — scheduled jobs

The API container applies pending yoyo migrations before starting Uvicorn.

The API is exposed at `http://localhost:8000` and the health endpoint is:

```text
GET /health
```

FastAPI's interactive API docs are available from the API application at `/docs`.

## Makefile workflow

The repository includes a Makefile for the common development operations:

```bash
make help
make start
make stop
make status
make health
make routes

make start-db
make dbshell
make upgrade
make migrate-new m="describe migration"

make logs
make logs-worker
make shell
```

`make fresh` destroys local data and rebuilds the full stack, so use it intentionally.

## Run locally without Docker

You still need PostgreSQL and Redis running.

```bash
uv sync
uv run yoyo apply --batch --database "$DATABASE_URL" ./migrations/yoyo
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Run workers in separate terminals:

```bash
uv run python -m saq saq_worker.settings
uv run cron_worker.py
```

## API surface

All application routers are mounted under `/api`.

Major groups include:

- `/api/auth/*` — register/login/logout, Google OAuth, current user, settings, dashboard, navigation links, notification SSE
- chapter endpoints — editing, publishing, comments, ordering, and chapter-level operations
- story endpoints — story lifecycle, scenes, search, analysis, and chat threads

Google OAuth flow:

```text
GET /api/auth/google/login
    -> Google
    -> GET /api/auth/google/callback
    -> create/link Nexus user
    -> create Nexus session
    -> set HttpOnly session cookie
    -> redirect to frontend
```

Password and OAuth authentication both converge on the same application session model.

## Story agent and search

The story agent is grounded against Nexus Writer's own data rather than relying only on model memory. Its tools can retrieve and search story evidence such as:

- scenes and full chapters
- tags, entities, points of view, and extracted metadata
- semantic/full-text search results
- structured internal story analytics

Chat is story-scoped and thread-based. Responses stream to the client with Server-Sent Events.

Search combines PostgreSQL full-text retrieval with vector similarity over scene embeddings, then fuses the candidate sets before returning results.

## Background processing

The SAQ worker handles queued derived work such as extraction/analysis jobs. The cron worker handles periodic maintenance and processing, including session cleanup and embedding/extraction sweeps.

Background jobs treat queued payloads as a request to do work, not as canonical truth: workers re-read current database state and avoid committing results derived from stale source state.

## Testing

Run the backend test suite with:

```bash
uv run pytest
```

Tests are split across:

```text
tests/
├── app/
├── data/
├── infrastructure/
├── service/
└── workers/
```

The suite includes ordinary service/repository tests plus adversarial tests for concurrency, stale writes, uniqueness races, retry/idempotency behavior, auth boundaries, worker redelivery, and real PostgreSQL transaction semantics.

Pull requests to `main` run CI with real PostgreSQL + pgvector and Redis services, apply migrations, then execute the full pytest suite.

## Migrations

This project uses **yoyo migrations**, not Alembic.

```bash
# apply pending migrations
uv run yoyo apply --batch --database "$DATABASE_URL" ./migrations/yoyo

# rollback
uv run yoyo rollback --batch --database "$DATABASE_URL" ./migrations/yoyo
```

Or use the Makefile helpers:

```bash
make upgrade
make migrate-new m="add something"
make migrate-history
```

## Frontend

The React SPA is maintained separately:

**https://github.com/AbdullaK123/nexus-writer-frontend-spa**

Run the frontend against this API with `VITE_API_BASE_URL=http://localhost:8000/api`.
