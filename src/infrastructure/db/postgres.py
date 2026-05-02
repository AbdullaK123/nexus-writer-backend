"""Postgres connection helpers.

The application uses asyncpg directly via the pool in
`src.infrastructure.db.pool`; this module only owns the URL building so
both the pool and any ad-hoc clients (yoyo, scripts, …) agree on the
same parameter set.
"""
from urllib.parse import urlencode, urlparse, urlunparse

from src.infrastructure.config.settings import settings, config


def build_database_url() -> str:
    """Return the configured database URL with pool sizing query params
    appended. asyncpg picks these up automatically."""
    pool_params = urlencode(
        {
            "minsize": config.postgres.pool_min_size,
            "maxsize": config.postgres.pool_max_size,
            "max_inactive_connection_lifetime": config.postgres.max_inactive_connection_lifetime,
        }
    )
    parsed = urlparse(str(settings.database_url))
    existing_query = f"{parsed.query}&{pool_params}" if parsed.query else pool_params
    return urlunparse(parsed._replace(query=existing_query))
