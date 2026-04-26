#!/bin/bash
docker compose exec nexus-writer uv run --no-sync aerich migrate --name "$1"