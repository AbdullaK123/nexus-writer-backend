# Nexus Writer Backend

Backend API and worker services for Nexus Writer, with a Vite/React frontend in `frontend/`.

## What this repo contains

- **Backend API**: FastAPI app (`main.py`)
- **Background worker**: Python worker process (`worker.py`)
- **Frontend**: React + TypeScript + Vite app (`frontend/`)
- **Database migrations**: yoyo migrations (`migrations/yoyo/`)
- **Containerized local stack**: PostgreSQL + API + worker (`docker-compose.yml`)

## Tech stack (current)

### Backend
- Python 3.10+
- FastAPI
- Uvicorn
- asyncpg / psycopg2-binary
- yoyo-migrations
- loguru
- pydantic-settings
- openai + pydantic-ai

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
├── worker.py
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
- provider keys used by enabled services (for example OpenAI)

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

### 4) Start worker (separate terminal)
```bash
uv run worker.py
```

Health endpoint:
- `GET http://localhost:8000/health`

## Run with Docker Compose

```bash
docker-compose up --build
```

Services:
- `postgres-nexus` (pgvector/postgres)
- `nexus-writer` (FastAPI API)
- `worker` (background worker)

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

No automated end-to-end verification was run as part of this README simplification update.  
This update was intentionally kept simple and focused on aligning docs with current repository structure and commands.
