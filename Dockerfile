# Stage 1: UV binary — pin a version to avoid re-pulling on every build
FROM ghcr.io/astral-sh/uv:0.7.8 AS uv

# Stage 2: Application
FROM python:3.12-slim

# Combine apt install into a single cached layer
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv from the first stage
COPY --from=uv /uv /usr/local/bin/uv

# Copy dependency files first (for Docker cache)
COPY pyproject.toml uv.lock ./

ENV UV_PYTHON_VERSION=3.12
ENV UV_SYSTEM_PYTHON=1


# Install dependencies (as root) with uv cache mounted.
# --no-install-project skips building the project itself here so this layer
# stays cacheable on dep-only changes and doesn't need README.md / src yet.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --frozen --no-install-project

# Create the runtime user and hand over the venv + workdir
RUN useradd --system --create-home --shell /usr/sbin/nologin appuser
COPY --chown=appuser:appuser . .

# Now that the source (incl. README.md) is present, install the project itself.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --frozen --no-install-project

RUN mkdir -p /app/logs /app/migrations/models \
    && chown -R appuser:appuser /app

USER appuser

# --no-sync prevents `uv run` from trying to mutate the baked-in venv at
# runtime (which would attempt to install dev deps and fail).
CMD ["uv", "run", "--no-sync", "main.py"]