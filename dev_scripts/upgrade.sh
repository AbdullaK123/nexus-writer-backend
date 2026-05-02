#!/bin/bash
# Apply pending yoyo migrations against the dockerised dev DB.
set -e

DSN="${DATABASE_URL:-postgresql://nexus_user:password@localhost:5432/nexus_writer}"
uv run yoyo apply --batch --database "$DSN" ./migrations/yoyo
echo "✓ yoyo migrations applied"
