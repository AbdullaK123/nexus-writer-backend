"""ChapterRepository — raw asyncpg + SQL. Returns Pydantic ChapterRow.

Like StoryRepository, methods that participate in a transaction accept an
optional `executor` (an asyncpg.Connection); without one they run against
the pool.

The pointer-sync method is the interesting one — it computes prev/next for
every chapter in `path` in a single statement using `unnest(... WITH
ORDINALITY)` + `lag/lead` window functions. Combined with the deferrable
unique constraints on prev/next added in migration 00002, the bulk update
applies cleanly without intermediate-state violations.
"""
from __future__ import annotations

from typing import Any, Sequence

import asyncpg

from src.data.schemas.enums import generate_uuid
from src.data.schemas import ChapterRow


_CHAPTER_COLUMNS = """
    id, story_id, user_id, title, content, published, word_count,
    next_chapter_id, prev_chapter_id,
    scenes_need_reextraction, scenes_extracted_at,
    created_at, updated_at
"""

# Same alias as in story.py — duplicated to avoid an import cycle and stay
# explicit about what each repo accepts. Typed as Any because asyncpg's
# Connection is a generic alias that pyright won't accept in a Union.
Executor = Any


class ChapterRepository:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    @property
    def pool(self) -> asyncpg.Pool:
        return self._pool

    def _exe(self, executor: Executor) -> Executor:
        return executor if executor is not None else self._pool

    async def get(
        self,
        chapter_id: str,
        user_id: str,
        *,
        executor: Executor | None = None,
    ) -> ChapterRow | None:
        sql = f'SELECT {_CHAPTER_COLUMNS} FROM "chapter" WHERE id = $1 AND user_id = $2'
        row = await self._exe(executor).fetchrow(sql, chapter_id, user_id)
        return ChapterRow.model_validate(dict(row)) if row else None

    async def get_for_system(
        self, chapter_id: str,
    ) -> ChapterRow | None:
        """System-level fetch (no user scoping). Used by background jobs
        like the scene extractor that don't have a user_id in scope."""
        sql = f'SELECT {_CHAPTER_COLUMNS} FROM "chapter" WHERE id = $1'
        row = await self._pool.fetchrow(sql, chapter_id)
        return ChapterRow.model_validate(dict(row)) if row else None

    async def get_with_story_title(
        self, chapter_id: str, user_id: str,
    ) -> tuple[ChapterRow, str] | None:
        """Returns the chapter plus its parent story's title in one round-trip.
        Lets callers build ChapterContentResponse without a second fetch."""
        sql = f"""
            SELECT {_CHAPTER_COLUMNS}, s.title AS story_title
              FROM "chapter" c
              JOIN "story" s ON s.id = c.story_id
             WHERE c.id = $1 AND c.user_id = $2
        """
        # qualified column names — the SELECT above is sloppy because
        # _CHAPTER_COLUMNS isn't aliased; expand it.
        sql = f"""
            SELECT
                c.id, c.story_id, c.user_id, c.title, c.content, c.published,
                c.word_count, c.next_chapter_id, c.prev_chapter_id,
                c.created_at, c.updated_at,
                s.title AS story_title
              FROM "chapter" c
              JOIN "story" s ON s.id = c.story_id
             WHERE c.id = $1 AND c.user_id = $2
        """
        row = await self._pool.fetchrow(sql, chapter_id, user_id)
        if row is None:
            return None
        d = dict(row)
        story_title = d.pop("story_title")
        return ChapterRow.model_validate(d), story_title

    async def list_by_story(
        self,
        story_id: str,
        user_id: str,
        *,
        executor: Executor | None = None,
    ) -> list[ChapterRow]:
        sql = f"""
            SELECT {_CHAPTER_COLUMNS} FROM "chapter"
             WHERE story_id = $1 AND user_id = $2
             ORDER BY created_at DESC
        """
        rows = await self._exe(executor).fetch(sql, story_id, user_id)
        return [ChapterRow.model_validate(dict(r)) for r in rows]

    async def list_by_story_ids(
        self, story_ids: Sequence[str],
    ) -> list[ChapterRow]:
        if not story_ids:
            return []
        sql = f"""
            SELECT {_CHAPTER_COLUMNS} FROM "chapter"
             WHERE story_id = ANY($1::TEXT[])
        """
        rows = await self._pool.fetch(sql, list(story_ids))
        return [ChapterRow.model_validate(dict(r)) for r in rows]

    async def create(
        self,
        *,
        story_id: str,
        user_id: str,
        title: str,
        content: str,
        word_count: int,
        executor: Executor | None = None,
    ) -> ChapterRow:
        sql = f"""
            INSERT INTO "chapter"
                (id, story_id, user_id, title, content, published,
                 word_count, next_chapter_id, prev_chapter_id,
                 created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, FALSE, $6, NULL, NULL, NOW(), NOW())
            RETURNING {_CHAPTER_COLUMNS}
        """
        row = await self._exe(executor).fetchrow(
            sql, generate_uuid(), story_id, user_id, title, content, word_count,
        )
        assert row is not None
        return ChapterRow.model_validate(dict(row))

    async def update(
        self,
        *,
        chapter_id: str,
        user_id: str,
        fields: dict[str, Any],
        executor: Executor | None = None,
    ) -> ChapterRow | None:
        if not fields:
            return await self.get(chapter_id, user_id, executor=executor)

        allowed = {"title", "content", "published", "word_count"}
        bad = set(fields) - allowed
        if bad:
            raise ValueError(f"unsupported fields: {sorted(bad)}")

        cols = list(fields.keys())
        set_clause = ", ".join(f"{col} = ${i + 3}" for i, col in enumerate(cols))
        params: list[Any] = [chapter_id, user_id, *fields.values()]

        sql = f"""
            UPDATE "chapter"
               SET {set_clause}, updated_at = NOW()
             WHERE id = $1 AND user_id = $2
            RETURNING {_CHAPTER_COLUMNS}
        """
        row = await self._exe(executor).fetchrow(sql, *params)
        return ChapterRow.model_validate(dict(row)) if row else None

    async def delete(
        self,
        *,
        chapter_id: str,
        user_id: str,
        executor: Executor | None = None,
    ) -> str | None:
        """Deletes the chapter, returning the story_id it belonged to (or None
        if no row was deleted). The story_id is needed by the caller to
        re-sync the parent story's path_array & pointers."""
        sql = """
            DELETE FROM "chapter"
             WHERE id = $1 AND user_id = $2
            RETURNING story_id
        """
        row = await self._exe(executor).fetchrow(sql, chapter_id, user_id)
        return row["story_id"] if row else None

    async def sync_pointers(
        self,
        story_id: str,
        path: Sequence[str],
        *,
        executor: Executor | None = None,
    ) -> None:
        """Set prev/next pointers for every chapter in `path` from the order
        of the array. Chapters in the table that are NOT in `path` are left
        alone (caller is responsible for delete bookkeeping).

        Implementation: one UPDATE that joins the chapter table against
        unnest(path WITH ORDINALITY), using lag/lead to compute neighbours.

        Safety: relies on the deferrable unique constraints on
        prev_chapter_id / next_chapter_id (migration 00002) — without them,
        bulk-swapping pointer values in a single statement would trip the
        per-row uniqueness check.
        """
        if not path:
            # Clear pointers for any chapters in this story (path is empty:
            # no ordering exists). Cheap safety net.
            await self._exe(executor).execute(
                """
                UPDATE "chapter"
                   SET prev_chapter_id = NULL,
                       next_chapter_id = NULL,
                       updated_at = NOW()
                 WHERE story_id = $1
                   AND (prev_chapter_id IS NOT NULL OR next_chapter_id IS NOT NULL)
                """,
                story_id,
            )
            return

        sql = """
            WITH ordered AS (
                SELECT
                    id,
                    LAG(id)  OVER (ORDER BY pos) AS prev_id,
                    LEAD(id) OVER (ORDER BY pos) AS next_id
                  FROM unnest($2::TEXT[]) WITH ORDINALITY AS t(id, pos)
            )
            UPDATE "chapter" c
               SET prev_chapter_id = o.prev_id,
                   next_chapter_id = o.next_id,
                   updated_at      = NOW()
              FROM ordered o
             WHERE c.id = o.id
               AND c.story_id = $1
        """
        await self._exe(executor).execute(sql, story_id, list(path))
