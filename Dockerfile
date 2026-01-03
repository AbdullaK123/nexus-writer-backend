# Stage 1: UV binary
FROM ghcr.io/astral-sh/uv:latest AS uv

# Stage 2: Application
FROM python:3.12-slim

RUN apt-get update && apt-get install -y build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv from the first stage
COPY --from=uv /uv /usr/local/bin/uv

# Copy dependency files first (for Docker cache)
COPY pyproject.toml uv.lock ./

# Ensure uv uses a CPython version that matches the lockfile
ENV UV_PYTHON_VERSION=3.12
ENV UV_SYSTEM_PYTHON=1

# Install dependencies
RUN uv sync

# Copy the rest of your code
COPY . .

CMD ["uv", "run", "main.py"]