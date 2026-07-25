# Nexus Writer Backend

Nexus Writer is a story-writing application with a FastAPI backend, background
workers, and a grounded story-research agent. The Vite/React frontend lives in
`frontend/`.

## What this repo contains

- **Backend API**: FastAPI app (`main.py`)
- **SAQ worker**: asynchronous scene-extraction and embedding jobs (`saq_worker.py`)
- **Cron worker**: scheduled maintenance and story-processing jobs (`cron_worker.py`)
- **Story agent**: tool-using chat assistant grounded in story scenes, chapters, and internal analytics
- **Frontend**: React + TypeScript + Vite app (`frontend/`)
- **Database migrations**: yoyo migrations (`migrations/yoyo/`)
- **Containerized local stack**: PostgreSQL, Redis, API, SAQ worker, and cron worker (`docker-compose.yml`)

## Tech stack (current)

### Backend
- Python 3.10+
- FastAPI
- Uvicorn
- asyncpg / psycopg2-binary
- yoyo-migrations
- loguru
- pydantic-settings
- OpenAI + OpenRouter
- pydantic-ai + pydantic-ai-harness
- Redis + SAQ

### Frontend
- React 19
- TypeScript
- Vite 8
- Ark UI
- TanStack Query / Router

## Project layout

```text
.
├── main.py
├── saq_worker.py
├── cron_worker.py
├── src/
│   ├── app/
│   │   ├── controllers/
│   │   ├── dependencies/
│   │   ├── middleware/
│   │   └── lifespan.py
│   ├── data/
│   ├── infrastructure/
│   ├── service/
│   └── shared/
├── migrations/
│   └── yoyo/
├── frontend/
│   ├── package.json
│   └── src/
└── docker-compose.yml
```

## Backend configuration

Create a `.env` file in the repository root. At minimum, provide values required by your runtime config (DB URLs, auth/cookie keys, and any AI/provider keys your enabled flows need).

Commonly used keys in this codebase include:

- `DATABASE_URL`
- `DATABASE_SYNC_URL`
- `MIGRATION_URL`
- `APP_SECRET_KEY`
- `COOKIE_SIGNING_KEY`
- `COOKIE_ENCRYPTION_KEY`
- `REDIS_URL`
- provider keys used by enabled services, including `OPENAI_API_KEY` and `OPEN_ROUTER_API_KEY`

Use your environment-specific values.

## Run locally (without Docker)

### 1) Install dependencies
```bash
uv sync
```

### 2) Apply migrations
```bash
uv run yoyo apply --batch --database "$MIGRATION_URL" ./migrations/yoyo
```

### 3) Start API
```bash
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4) Start the SAQ worker (separate terminal)
```bash
uv run python -m saq saq_worker.settings
```

### 5) Start the cron worker (separate terminal)
```bash
uv run cron_worker.py
```

Health endpoint:
- `GET http://localhost:8000/health`

## Run with Docker Compose

```bash
docker-compose up --build
```

Services:
- `postgres-nexus` (pgvector/postgres)
- `nexus-redis` (Redis)
- `nexus-writer` (FastAPI API)
- `saq-worker` (scene extraction and embedding jobs)
- `cron-worker` (scheduled jobs)

The API container applies yoyo migrations on startup, then starts Uvicorn.

## Frontend

From `frontend/`:

```bash
npm install
npm run dev
```

Available scripts:
- `npm run dev`
- `npm run build`
- `npm run lint`
- `npm run preview`

Node version requirement:
- `>=20.19`

## API routing (current)

`main.py` mounts routers under `/api`:
- auth controller
- chapter controller
- story controller

Also includes:
- `GET /health`

Story routes include chapter and scene operations, semantic scene search,
story vocabulary, Book Pulse, and thread-based agent chat streamed over SSE.

## Story Agent And Internal Analytics

Story analysis is agent-first. The chat agent is grounded with tools that can:

- search scenes semantically and filter by extracted story metadata
- retrieve full chapters or the exact prose of a located scene
- list chapters, tags, entities, and points of view
- inspect structured internal analytics for character, plot, structure, and world questions

The agent uses the internal `AnalyticsService` as research evidence alongside
scene and chapter retrieval. It is not a public dashboard API.

The dashboard UI and public `/api/stories/{story_id}/analytics/dashboard/*` endpoints
were retired on 2026-07-25. The former frontend UI remains under
`frontend/src/components/analytics/` as deprecated reference code; see its
`DEPRECATED.md` before considering restoration.

## Notes on logging and error handling

- Log configuration is initialized at startup (`configure_logger()`).
- Layered exception handlers exist for:
  - service errors
  - data errors
  - infrastructure errors
  - unhandled exceptions
- Correlation ID support is wired through shared utilities.

## Database migrations

This repository uses **yoyo migrations** (not Alembic) in:

- `migrations/yoyo/`

Typical commands:

```bash
# apply all
uv run yoyo apply --batch --database "$MIGRATION_URL" ./migrations/yoyo

# rollback one migration (example)
uv run yoyo rollback --batch --database "$MIGRATION_URL" ./migrations/yoyo
```

## Development helper scripts

`dev_scripts/` includes utility scripts for local workflows, such as starting/stopping DB and backend services.

## Testing status

Pytest dependencies are configured, but no `tests/` directory is currently
checked into this repository.
