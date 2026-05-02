#!/usr/bin/env bash
# Wrapper around yoyo CLI. Reads DATABASE_URL from the environment and
# normalises postgres:// → postgresql:// so yoyo's URL parser is happy.
#
# Usage:
#   ./dev_scripts/yoyo.sh apply               # apply pending migrations
#   ./dev_scripts/yoyo.sh new "add scenes"    # create a new migration
#   ./dev_scripts/yoyo.sh rollback            # rollback the latest
#   ./dev_scripts/yoyo.sh list                # show migration status
set -euo pipefail

if [[ -z "${DATABASE_URL:-}" ]]; then
    echo "DATABASE_URL is not set" >&2
    exit 1
fi

# yoyo wants postgresql:// (asyncpg accepts both)
db_url="${DATABASE_URL/postgres:\/\//postgresql:\/\/}"

cd "$(dirname "$0")/.."
exec yoyo "$@" --database "$db_url"
