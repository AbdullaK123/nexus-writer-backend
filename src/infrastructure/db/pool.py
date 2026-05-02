"""asyncpg connection pool — lifecycle owned by the FastAPI lifespan / worker.

Module-level singleton kept behind getters so callers can't accidentally
acquire before init() / after close(). Repositories receive the pool via DI.
"""
from __future__ import annotations

import json

import asyncpg
from loguru import logger

from src.infrastructure.config import config, settings


_pool: asyncpg.Pool | None = None


async def _setup_connection(conn: asyncpg.Connection) -> None:
    """Per-connection init. Registers a JSON/JSONB codec so columns round-trip
    as Python dicts/lists instead of strings."""
    await conn.set_type_codec(
        "jsonb",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )
    await conn.set_type_codec(
        "json",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )


async def init_pool() -> asyncpg.Pool:
    global _pool
    if _pool is not None:
        return _pool
    # asyncpg only accepts the bare `postgresql://` / `postgres://` scheme.
    # Tolerate the SQLAlchemy-style `postgresql+asyncpg://...` DSN that other
    # tools (alembic, yoyo, ORM configs) often want to share via .env.
    dsn = str(settings.database_url).replace(
        "postgresql+asyncpg://", "postgresql://", 1,
    )
    _pool = await asyncpg.create_pool(
        dsn=dsn,
        min_size=config.postgres.pool_min_size,
        max_size=config.postgres.pool_max_size,
        max_inactive_connection_lifetime=config.postgres.max_inactive_connection_lifetime,
        init=_setup_connection,
    )
    logger.info(
        "infra.pool.connected",
        min_size=config.postgres.pool_min_size,
        max_size=config.postgres.pool_max_size,
    )
    assert _pool is not None
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is None:
        return
    await _pool.close()
    _pool = None
    logger.info("infra.pool.disconnected")


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("asyncpg pool not initialised — call init_pool() first")
    return _pool
