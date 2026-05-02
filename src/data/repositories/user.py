"""UserRepository — raw asyncpg + SQL. Returns Pydantic UserRow."""
from __future__ import annotations

import asyncpg

from src.data.schemas import UserRow
from src.data.schemas.enums import generate_uuid


_USER_COLUMNS = """
    id, username, email, password_hash, profile_img,
    created_at, updated_at
"""


class UserRepository:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def get_by_id(self, user_id: str) -> UserRow | None:
        sql = f'SELECT {_USER_COLUMNS} FROM "user" WHERE id = $1'
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(sql, user_id)
        return UserRow.model_validate(dict(row)) if row else None

    async def get_by_email(self, email: str) -> UserRow | None:
        sql = f'SELECT {_USER_COLUMNS} FROM "user" WHERE email = $1'
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(sql, email)
        return UserRow.model_validate(dict(row)) if row else None

    async def create(
        self,
        *,
        username: str,
        email: str,
        password_hash: str,
        profile_img: str | None,
    ) -> UserRow:
        sql = f"""
            INSERT INTO "user"
                (id, username, email, password_hash, profile_img,
                 created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
            RETURNING {_USER_COLUMNS}
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                sql, generate_uuid(), username, email, password_hash, profile_img,
            )
        assert row is not None
        return UserRow.model_validate(dict(row))
