FROM python:3.12-slim

# Add this line:
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first (for Docker cache)
COPY pyproject.toml uv.lock ./

# Ensure uv uses a CPython version that matches the lockfile
ENV UV_PYTHON_VERSION=3.12

# Install dependencies
RUN uv sync

# Copy the rest of your code
COPY . .

CMD ["uv", "run", "main.py"]