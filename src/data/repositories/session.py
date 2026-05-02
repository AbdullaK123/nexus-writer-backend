"""SessionRepository — raw asyncpg + SQL. Returns Pydantic SessionRow."""
from __future__ import annotations

from datetime import datetime, timezone

import asyncpg

from src.data.schemas import SessionRow


_SESSION_COLUMNS = """
    session_id, user_id, expires_at, ip_address, user_agent,
    created_at, updated_at
"""


class SessionRepository:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def get(self, session_id: str) -> SessionRow | None:
        sql = f'SELECT {_SESSION_COLUMNS} FROM "session" WHERE session_id = $1'
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(sql, session_id)
        return SessionRow.model_validate(dict(row)) if row else None

    async def create(
        self,
        *,
        session_id: str,
        user_id: str,
        expires_at: datetime,
        ip_address: str | None,
        user_agent: str | None,
    ) -> SessionRow:
        sql = f"""
            INSERT INTO "session"
                (session_id, user_id, expires_at, ip_address, user_agent,
                 created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
            RETURNING {_SESSION_COLUMNS}
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                sql, session_id, user_id, expires_at, ip_address, user_agent,
            )
        assert row is not None
        return SessionRow.model_validate(dict(row))

    async def delete(self, session_id: str) -> bool:
        """Delete a session. Returns True if a row was actually removed."""
        sql = 'DELETE FROM "session" WHERE session_id = $1'
        async with self._pool.acquire() as conn:
            status = await conn.execute(sql, session_id)
        # asyncpg returns "DELETE <n>"
        return status.endswith(" 1")

    async def delete_expired(self) -> int:
        """Delete all sessions with expires_at < now. Returns count removed."""
        sql = 'DELETE FROM "session" WHERE expires_at < $1'
        async with self._pool.acquire() as conn:
            status = await conn.execute(sql, datetime.now(timezone.utc))
        # "DELETE 7" → 7
        return int(status.split()[-1])
