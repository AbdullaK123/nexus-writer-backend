#!/bin/bash
# Wipe DB + migrations dir, then regenerate a single baseline migration.
# Use when stabilizing schema before the first real release.
set -e

docker compose down -v postgres-nexus
docker compose up -d postgres-nexus

until docker compose exec -T postgres-nexus pg_isready -U nexus_user -d nexus_writer >/dev/null 2>&1; do
  sleep 0.5
done

rm -rf migrations/models/*
docker compose exec nexus-writer uv run --no-sync aerich init-db
echo "✓ Fresh baseline migration created in migrations/models/"
