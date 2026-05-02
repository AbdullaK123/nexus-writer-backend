"""Database-pool FastAPI dependency.

Lives in its own module so both `repositories.py` and `services.py` can
import it without creating a cycle (repositories <- services <- repositories).
"""
import asyncpg
from fastapi import Request

from src.infrastructure.db.pool import get_pool


def get_db_pool(request: Request) -> asyncpg.Pool:
    """FastAPI dependency. Reads the pool initialised in the lifespan.
    Override in tests via app.dependency_overrides."""
    return get_pool()
