"""StoryRepository — raw asyncpg + SQL. Returns Pydantic StoryRow.

Methods that participate in a multi-statement transaction accept an optional
`executor` (an `asyncpg.Connection`); when not supplied they run against the
pool directly (which acquires-and-releases a connection per call). asyncpg's
Pool exposes `fetch`/`fetchrow`/`execute` with that exact contract, so the
two are interchangeable for single-shot calls.
"""
from __future__ import annotations

from typing import Any, Sequence

import asyncpg

from src.data.schemas.enums import generate_uuid
from src.data.schemas import StoryRow


_STORY_COLUMNS = """
    id, user_id, title, story_context, status, path_array,
    created_at, updated_at
"""


# Anything supporting asyncpg's fetchrow/fetch/execute contract: a Pool or a
# Connection. Typed as `Any` because asyncpg's Connection is a generic alias
# (Connection[Record]) that pyright won't accept in a Union.
Executor = Any


class StoryRepository:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    @property
    def pool(self) -> asyncpg.Pool:
        return self._pool

    def _exe(self, executor: Executor) -> Executor:
        return executor if executor is not None else self._pool

    async def get(
        self, story_id: str, user_id: str, *, executor: Executor | None = None,
    ) -> StoryRow | None:
        sql = f'SELECT {_STORY_COLUMNS} FROM "story" WHERE id = $1 AND user_id = $2'
        row = await self._exe(executor).fetchrow(sql, story_id, user_id)
        return StoryRow.model_validate(dict(row)) if row else None

    async def list_for_user(self, user_id: str) -> list[StoryRow]:
        sql = f"""
            SELECT {_STORY_COLUMNS} FROM "story"
             WHERE user_id = $1
             ORDER BY created_at DESC
        """
        rows = await self._pool.fetch(sql, user_id)
        return [StoryRow.model_validate(dict(r)) for r in rows]

    async def exists_with_title(self, user_id: str, title: str) -> bool:
        sql = 'SELECT 1 FROM "story" WHERE user_id = $1 AND title = $2'
        row = await self._pool.fetchrow(sql, user_id, title)
        return row is not None

    async def create(self, *, user_id: str, title: str) -> StoryRow:
        sql = f"""
            INSERT INTO "story"
                (id, user_id, title, story_context, status, path_array,
                 created_at, updated_at)
            VALUES ($1, $2, $3, NULL, 'Ongoing', ARRAY[]::TEXT[], NOW(), NOW())
            RETURNING {_STORY_COLUMNS}
        """
        row = await self._pool.fetchrow(sql, generate_uuid(), user_id, title)
        assert row is not None
        return StoryRow.model_validate(dict(row))

    async def update(
        self,
        *,
        story_id: str,
        user_id: str,
        fields: dict[str, Any],
    ) -> StoryRow | None:
        """Partial update. Empty `fields` is a no-op (returns current row)."""
        if not fields:
            return await self.get(story_id, user_id)

        # Build SET clause dynamically. Whitelisted columns only — never let
        # arbitrary keys in. The `fields` dict already comes from a Pydantic
        # model, but defense-in-depth.
        allowed = {"title", "status", "story_context"}
        bad = set(fields) - allowed
        if bad:
            raise ValueError(f"unsupported fields: {sorted(bad)}")

        cols = list(fields.keys())
        set_clause = ", ".join(f'{col} = ${i + 3}' for i, col in enumerate(cols))
        params: list[Any] = [story_id, user_id, *fields.values()]

        sql = f"""
            UPDATE "story"
               SET {set_clause}, updated_at = NOW()
             WHERE id = $1 AND user_id = $2
            RETURNING {_STORY_COLUMNS}
        """
        row = await self._pool.fetchrow(sql, *params)
        return StoryRow.model_validate(dict(row)) if row else None

    async def delete(self, *, story_id: str, user_id: str) -> bool:
        sql = 'DELETE FROM "story" WHERE id = $1 AND user_id = $2'
        status = await self._pool.execute(sql, story_id, user_id)
        return status.endswith(" 1")

    async def set_path_array(
        self,
        story_id: str,
        path: Sequence[str],
        *,
        executor: Executor | None = None,
    ) -> None:
        sql = """
            UPDATE "story"
               SET path_array = $2::TEXT[],
                   updated_at = NOW()
             WHERE id = $1
        """
        await self._exe(executor).execute(sql, story_id, list(path))

    async def get_path_array(
        self, story_id: str, *, executor: Executor | None = None,
    ) -> list[str] | None:
        """Returns the story's path_array, or None if the story doesn't exist.
        Distinguishes 'no story' from 'empty path' on purpose."""
        sql = 'SELECT path_array FROM "story" WHERE id = $1'
        row = await self._exe(executor).fetchrow(sql, story_id)
        if row is None:
            return None
        return list(row["path_array"] or [])

    async def touch(
        self, story_id: str, *, executor: Executor | None = None,
    ) -> None:
        sql = 'UPDATE "story" SET updated_at = NOW() WHERE id = $1'
        await self._exe(executor).execute(sql, story_id)
