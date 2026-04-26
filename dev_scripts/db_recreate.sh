#!/bin/bash
# Drop & recreate schema directly from Tortoise models. No migrations involved.
# Use during early dev when the schema is in flux.
set -e

docker compose down -v postgres-nexus
docker compose up -d postgres-nexus

# Wait for postgres to accept connections.
until docker compose exec -T postgres-nexus pg_isready -U nexus_user -d nexus_writer >/dev/null 2>&1; do
  sleep 0.5
done

docker compose exec -T nexus-writer uv run --no-sync python -c "
import asyncio
from tortoise import Tortoise
from src.infrastructure.db.postgres import TORTOISE_ORM

async def go():
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas(safe=False)
    await Tortoise.close_connections()

asyncio.run(go())
"
echo "✓ Schema regenerated from models"
