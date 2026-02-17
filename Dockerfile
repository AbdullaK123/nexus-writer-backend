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


# Install dependencies with uv cache mounted — avoids re-downloading on rebuilds
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --frozen

# Copy the rest of your code
RUN useradd --system --create-home --shell /usr/sbin/nologin appuser
RUN mkdir -p /app/logs && chown appuser:appuser /app/logs
COPY --chown=appuser:appuser . .

USER appuser

CMD ["uv", "run", "main.py"]