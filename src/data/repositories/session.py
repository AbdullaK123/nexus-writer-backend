"""SessionRepository — raw asyncpg + SQL. Returns Pydantic SessionRow."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import asyncpg

from src.data.schemas import SessionRow


_SESSION_COLUMNS = """
    session_id, user_id, expires_at, ip_address, user_agent,
    created_at, updated_at
"""

Executor = Any


class SessionRepository:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    @property
    def pool(self) -> asyncpg.Pool:
        return self._pool

    def _exe(self, executor: Executor | None) -> Executor:
        return executor if executor is not None else self._pool

    async def get(
        self,
        session_id: str,
        executor: Executor | None = None,
    ) -> SessionRow | None:
        sql = f'SELECT {_SESSION_COLUMNS} FROM "session" WHERE session_id = $1'
        row = await self._exe(executor).fetchrow(sql, session_id)
        return SessionRow.model_validate(dict(row)) if row else None

    async def create(
        self,
        *,
        session_id: str,
        user_id: str,
        expires_at: datetime,
        ip_address: str | None,
        user_agent: str | None,
        executor: Executor | None = None,
    ) -> SessionRow:
        sql = f"""
            INSERT INTO "session"
                (session_id, user_id, expires_at, ip_address, user_agent,
                 created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
            RETURNING {_SESSION_COLUMNS}
        """
        row = await self._exe(executor).fetchrow(
            sql,
            session_id,
            user_id,
            expires_at,
            ip_address,
            user_agent,
        )
        assert row is not None
        return SessionRow.model_validate(dict(row))

    async def delete(
        self,
        session_id: str,
        executor: Executor | None = None,
    ) -> bool:
        sql = 'DELETE FROM "session" WHERE session_id = $1'
        status = await self._exe(executor).execute(sql, session_id)
        return status.endswith(" 1")

    async def delete_all(
        self,
        user_id: str,
        executor: Executor | None = None,
    ) -> bool:
        sql = 'DELETE FROM "session" WHERE user_id = $1'
        status = await self._exe(executor).execute(sql, user_id)
        return not status.endswith(" 0")

    async def delete_expired(
        self,
        executor: Executor | None = None,
    ) -> int:
        sql = 'DELETE FROM "session" WHERE expires_at < $1'
        status = await self._exe(executor).execute(sql, datetime.now(timezone.utc))
        return int(status.split()[-1])