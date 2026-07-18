"""SceneRepository — one row per extracted scene, plus per-chapter staleness
tracking on the `chapter` table.

Replaces the old ExtractionRepository which stored scenes as a JSONB blob.
The big shape change: extraction is no longer an upsert against a single row.
Instead, `replace_for_chapter` deletes-then-bulk-inserts inside a transaction
so a re-extraction atomically swaps the scene set for a chapter.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from time import perf_counter
from typing import Any, List, Literal, Sequence

import asyncpg
from loguru import logger
from uuid_extensions import uuid7str

from src.data.schemas import Scene, SceneRow
from src.data.schemas.scene import SceneSearchResult
from src.shared.utils.html import get_word_count, html_to_plain_text


_SCENE_COLUMNS = """
    id, chapter_id, story_id, user_id, position,
    title, start_quote, end_quote, description, pov,
    tension, pacing, mentioned_entities, tags, questions_raised,
    embedding_model, embedded_at, created_at, updated_at
"""

# `embedding` is intentionally excluded from the default projection — it's a
# pgvector value asyncpg surfaces as text, big, and rarely needed by the API.
# Read it explicitly when running similarity queries.

Executor = Any


class SceneRepository:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    @property
    def pool(self) -> asyncpg.Pool:
        return self._pool

    def _exe(self, executor: Executor) -> Executor:
        return executor if executor is not None else self._pool

    # ─── reads ────────────────────────────────────────────────────────────

    async def list_by_chapter(
        self, chapter_id: str, *, executor: Executor | None = None,
    ) -> list[SceneRow]:
        sql = f"""
            SELECT {_SCENE_COLUMNS}
              FROM "scene"
             WHERE chapter_id = $1
             ORDER BY position ASC
        """
        rows = await self._exe(executor).fetch(sql, chapter_id)
        return [SceneRow.model_validate(dict(r)) for r in rows]
    
    async def get_scene_text(
        self, 
        chapter_id: str, 
        start_quote: str,
        end_quote: str,
        *, 
        executor: Executor | None = None
    ) -> str | None:

        chapter_text_sql =f"""\
        SELECT content
        FROM "chapter"
        WHERE id = $1
        """

        chapter_text_raw = await self._exe(executor).fetchrow(chapter_text_sql, chapter_id)

        chapter_plain_text = html_to_plain_text(chapter_text_raw["content"])

        start_idx = chapter_plain_text.find(start_quote)
        if start_idx == -1:
            return None
        end_idx = chapter_plain_text.find(end_quote)
        if end_idx == -1:
            return None
        
        return chapter_plain_text[start_idx : end_idx + len(end_quote)]

    async def get_scene_word_count(
        self, 
        chapter_id: str, 
        start_quote: str,
        end_quote: str,
        *, 
        executor: Executor | None = None
    ) -> int:
        
        scene_text = await self.get_scene_text(chapter_id, start_quote, end_quote)

        if scene_text is None:
            return 0
        
        return len(scene_text.split())


    async def list_by_story(
        self, story_id: str, user_id: str, *, chapter_id: str | None = None, executor: Executor | None = None,
    ) -> list[SceneRow]:

        sql = f"""
            WITH story_ids AS (
                SELECT UNNEST(
                    path_array[1 : COALESCE(
                        array_position(path_array, $3),
                        cardinality(path_array)
                    )]
                ) AS chapter_id
                FROM story
                WHERE id = $1
            )
            SELECT {_SCENE_COLUMNS}
            FROM "scene"
            WHERE story_id = $1 
                AND user_id = $2
                AND chapter_id IN (SELECT chapter_id FROM story_ids)
            ORDER BY chapter_id, position ASC
        """
        rows = await self._exe(executor).fetch(sql, story_id, user_id, chapter_id)
        return [SceneRow.model_validate(dict(r)) for r in rows]

    async def list_pending_embeddings(
        self, *, limit: int, executor: Executor | None = None,
    ) -> list[SceneRow]:
        """Scenes with no embedding yet — input for the embedding worker.
        Ordered oldest-first so old work doesn't starve."""
        sql = f"""
            SELECT {_SCENE_COLUMNS}
              FROM "scene"
             WHERE embedding IS NULL
             ORDER BY created_at ASC
             LIMIT $1
        """
        rows = await self._exe(executor).fetch(sql, limit)
        return [SceneRow.model_validate(dict(r)) for r in rows]

    # ─── writes ───────────────────────────────────────────────────────────

    async def replace_for_chapter(
        self,
        *,
        chapter_id: str,
        story_id: str,
        user_id: str,
        scenes: Sequence[Scene],
        executor: Executor | None = None,
    ) -> None:
        """Atomically replace this chapter's scenes with `scenes`. Wipes any
        existing scenes (and their embeddings) and inserts the new set.

        Requires either a caller-provided transactional executor OR will
        acquire a connection and run its own transaction. Either way the
        delete+insert pair is atomic.
        """
        if executor is None:
            async with self._pool.acquire() as conn:
                async with conn.transaction():
                    await self._replace_for_chapter_inner(
                        conn, chapter_id, story_id, user_id, scenes,
                    )
            return

        await self._replace_for_chapter_inner(
            executor, chapter_id, story_id, user_id, scenes,
        )

    async def _replace_for_chapter_inner(
        self,
        conn: Any,
        chapter_id: str,
        story_id: str,
        user_id: str,
        scenes: Sequence[Scene],
    ) -> None:
        await conn.execute('DELETE FROM "scene" WHERE chapter_id = $1', chapter_id)
        if not scenes:
            return

        rows = [
            (
                uuid7str(),
                chapter_id, story_id, user_id, position,
                scene.title, scene.start_quote, scene.end_quote, scene.description, scene.pov,
                scene.tension, scene.pacing,
                scene.mentioned_entities, scene.tags, scene.questions_raised, self.get_scene_word_count(chapter_id, scene.start_quote, scene.end_quote)
            )
            for position, scene in enumerate(scenes)
        ]
        # asyncpg.copy_records_to_table beats per-row INSERT for any non-trivial
        # batch and skips the round-trip-per-row overhead.
        await conn.copy_records_to_table(
            "scene",
            records=rows,
            columns=[
                "id", "chapter_id", "story_id", "user_id", "position",
                "title", "start_quote", "end_quote", "description", "pov",
                "tension", "pacing", "mentioned_entities", "tags",
                "questions_raised", "word_count"
            ],
        )

    async def update_embedding(
        self,
        *,
        scene_id: str,
        embedding: Sequence[float],
        embedding_model: str,
        executor: Executor | None = None,
    ) -> None:
        """Patch in an embedding vector. Called by the embedding worker —
        application code never reads `embedding` directly here.

        `embedding` is a list[float]; pgvector accepts it via str cast.
        """
        sql = """
            UPDATE "scene"
               SET embedding = $2::vector,
                   embedding_model = $3,
                   embedded_at = NOW(),
                   updated_at = NOW()
             WHERE id = $1
        """
        # pgvector text format: '[1.0,2.0,3.0]'
        embedding_text = "[" + ",".join(repr(float(x)) for x in embedding) + "]"
        await self._exe(executor).execute(
            sql, scene_id, embedding_text, embedding_model,
        )

    # ─── chapter-level extraction status ───────────────────────────────────

    async def mark_chapter_stale(
        self, chapter_id: str, *, executor: Executor | None = None,
    ) -> None:
        """Flag a chapter for re-extraction. Idempotent."""
        sql = """
            UPDATE "chapter"
               SET scenes_need_reextraction = TRUE,
                   updated_at = NOW()
             WHERE id = $1
        """
        await self._exe(executor).execute(sql, chapter_id)

    async def mark_chapter_extracted(
        self, chapter_id: str, *, executor: Executor | None = None,
    ) -> None:
        """Clear the stale flag and stamp `scenes_extracted_at`. Called at
        the end of a successful extraction, inside the same transaction."""
        sql = """
            UPDATE "chapter"
               SET scenes_need_reextraction = FALSE,
                   scenes_extracted_at = NOW(),
                   updated_at = NOW()
             WHERE id = $1
        """
        await self._exe(executor).execute(sql, chapter_id)

    async def list_stale_chapter_ids(
        self,
        *,
        window_seconds: int,
        limit: int,
        executor: Executor | None = None,
    ) -> list[str]:
        """Chapters flagged for re-extraction whose last edit is older than
        `window_seconds` (debounce — don't re-extract while the user is
        actively typing). Ordered oldest-first."""
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
        sql = """
            SELECT id
              FROM "chapter"
             WHERE scenes_need_reextraction = TRUE
               AND updated_at <= $1
             ORDER BY updated_at ASC
             LIMIT $2
        """
        rows = await self._exe(executor).fetch(sql, cutoff, limit)
        return [r["id"] for r in rows]
    

    async def search_scenes(
        self,
        *,
        user_id: str,
        story_id: str | None,
        query_text: str,
        query_embedding: Sequence[float],
        k: int,
        candidate_pool: int,
        tension: Literal["low", "medium", "high"] | None = None,
        pacing: Literal["slow", "steady", "fast"] | None = None,
        tags: list[str] | None = None,
        pov: str | None = None,
        mentioned_entities: list[str] | None = None,
        chapter_ids: list[str] | None = None,
        executor: Executor | None = None,
    ) -> list[SceneSearchResult]:
        embedding_text = "[" + ",".join(repr(float(x)) for x in query_embedding) + "]"
        # Hybrid search via Reciprocal Rank Fusion of two CTEs:
        #   * `fts`: native Postgres FTS, ranked by ts_rank_cd. Lexical hits.
        #   * `vec`: pgvector cosine distance. Semantic hits.
        # We use Postgres-native FTS (not pg_textsearch / BM25) so this works
        # on Neon and other managed providers.
        #
        # The to_tsvector(...) expression here MUST match the index expression
        # in migration scene-fts-index literally for the planner to use the
        # GIN index. Change one → change both.
        # Indexed text is just title + description; arrays are skipped on the
        # lexical side because array_to_string isn't IMMUTABLE. The vector
        # CTE still covers tags / questions_raised via the embedded text.

        sql = f"""
            WITH fts AS (
                SELECT id,
                    ROW_NUMBER() OVER (
                        ORDER BY ts_rank_cd(
                            to_tsvector(
                                'english'::regconfig,
                                coalesce(title, '') || ' ' || coalesce(description, '')
                            ),
                            websearch_to_tsquery('english', $3::text)
                        ) DESC
                    ) AS rank
                FROM "scene"
                WHERE user_id = $1
                AND ($2::text IS NULL OR story_id = $2)
                AND ($7::text IS NULL OR tension = $7)
                AND ($8::text IS NULL OR pacing = $8)
                AND ($9::text[] IS NULL OR tags && $9::text[])
                AND ($10::text[] IS NULL OR mentioned_entities && $10::text[])
                AND ($11::text[] IS NULL OR chapter_id = ANY($11::text[]))
                AND ($12::text IS NULL OR pov = $12)
                AND to_tsvector(
                        'english'::regconfig,
                        coalesce(title, '') || ' ' || coalesce(description, '')
                    ) @@ websearch_to_tsquery('english', $3::text)
                ORDER BY ts_rank_cd(
                    to_tsvector(
                        'english'::regconfig,
                        coalesce(title, '') || ' ' || coalesce(description, '')
                    ),
                    websearch_to_tsquery('english', $3::text)
                ) DESC
                LIMIT $5
            ),
            vec AS (
                SELECT id,
                    ROW_NUMBER() OVER (ORDER BY embedding <=> $4::vector) AS rank
                FROM "scene"
                WHERE user_id = $1
                AND ($7::text IS NULL OR tension = $7)
                AND ($8::text IS NULL OR pacing = $8)
                AND ($9::text[] IS NULL OR tags && $9::text[])
                AND ($10::text[] IS NULL OR mentioned_entities && $10::text[])
                AND ($11::text[] IS NULL OR chapter_id = ANY($11::text[]))
                AND ($12::text IS NULL OR pov = $12)
                AND ($2::text IS NULL OR story_id = $2)
                AND embedding IS NOT NULL
                ORDER BY embedding <=> $4::vector
                LIMIT $5
            ),
            ranked AS (
                SELECT COALESCE(f.id, v.id) AS id,
                    COALESCE(1.0 / (5.0 + f.rank), 0)
                    + COALESCE(1.0 / (5.0 + v.rank), 0) AS score
                FROM fts f FULL OUTER JOIN vec v USING (id)
                ORDER BY score DESC
                LIMIT $6
            )
            SELECT 
                s.id AS id, 
                s.chapter_id AS chapter_id, 
                s.story_id AS story_id, 
                s.user_id AS user_id, 
                s.position AS position, 
                s.title AS title, 
                s.start_quote AS start_quote, 
                s.end_quote AS end_quote, 
                s.description AS description, 
                s.pov AS pov,
                s.tension AS tension, 
                s.pacing AS pacing, 
                s.mentioned_entities AS mentioned_entities, 
                s.tags AS tags, 
                s.questions_raised AS questions_raised, 
                s.word_count AS word_count,
                s.embedding_model AS embedding_model, 
                s.embedded_at AS embedded_at, 
                s.created_at AS created_at, 
                s.updated_at AS updated_at, 
                c.title AS chapter_title,
                r.score AS score
            FROM "scene" s
            INNER JOIN "chapter" c ON (s.chapter_id = c.id)
            JOIN ranked r ON (s.id = r.id) 
            ORDER BY r.score DESC
        """
        t0 = perf_counter()
        rows = await self._exe(executor).fetch(
            sql, 
            user_id, 
            story_id, 
            query_text, 
            embedding_text, 
            candidate_pool, 
            k,
            tension,
            pacing,
            tags,
            mentioned_entities,
            chapter_ids,
            pov
        )
        logger.info(
            "scene_repo.search_scenes.done",
            user_id=user_id,
            story_id=story_id,
            query_len=len(query_text),
            k=k,
            candidate_pool=candidate_pool,
            results=len(rows),
            ms=round((perf_counter() - t0) * 1000, 1),
        )
        return [
            SceneSearchResult(
                id=r["id"],
                chapter_id=r["chapter_id"],
                story_id=r["story_id"],
                user_id=r["user_id"],
                position=r["position"],
                title=r["title"],
                start_quote=r["start_quote"],
                end_quote=r["end_quote"],
                description=r["description"],
                pov=r["pov"],
                word_count=r["word_count"],
                tension=r["tension"],
                pacing=r["pacing"],
                mentioned_entities=r["mentioned_entities"],
                tags=r["tags"],
                questions_raised=r["questions_raised"],
                embedding_model=r["embedding_model"],
                embedded_at=r["embedded_at"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
                chapter_title=r["chapter_title"],
                score=r["score"]
            )
            for r in rows
        ]

    # ─── vocabulary listing ───────────────────────────────────────────────
    # Used by the agent to discover what tag / entity strings actually exist
    # for a given story before issuing a filtered search. Both columns are
    # text[]; unnest + group by gives a frequency-sorted vocabulary in one
    # round trip. Authorization is enforced row-level via user_id.

    async def list_story_tags(
        self,
        *,
        user_id: str,
        story_id: str,
        executor: Executor | None = None,
    ) -> list[tuple[str, int]]:
        sql = """
            SELECT tag, COUNT(*) AS n
            FROM "scene", unnest(tags) AS tag
            WHERE user_id = $1 AND story_id = $2
            GROUP BY tag
            ORDER BY n DESC, tag ASC
        """
        rows = await self._exe(executor).fetch(sql, user_id, story_id)
        return [(r["tag"], r["n"]) for r in rows]

    async def list_story_entities(
        self,
        *,
        user_id: str,
        story_id: str,
        executor: Executor | None = None,
    ) -> list[tuple[str, int]]:
        sql = """
            SELECT entity, COUNT(*) AS n
            FROM "scene", unnest(mentioned_entities) AS entity
            WHERE user_id = $1 AND story_id = $2
            GROUP BY entity
            ORDER BY n DESC, entity ASC
        """
        rows = await self._exe(executor).fetch(sql, user_id, story_id)
        return [(r["entity"], r["n"]) for r in rows]
    
    async def list_povs(
        self,
        *,
        user_id: str,
        story_id: str,
        executor: Executor | None = None
    ) -> list[tuple[str, int]]:
        sql = """\
        SELECT pov, COUNT(*) AS n
        FROM "scene"
        WHERE user_id = $1 AND story_id = $2
        GROUP BY pov
        ORDER BY n DESC
        """
        rows = await self._exe(executor).fetch(sql, user_id, story_id)
        return [(r["pov"], r["n"]) for r in rows]