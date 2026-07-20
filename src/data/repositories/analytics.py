from typing import Any
import asyncpg
type Executor = Any


class AnalyticsRepository:

    def __init__(
        self,
        pool: asyncpg.Pool
    ):
        self._pool = pool

    @property
    def pool(self) -> asyncpg.Pool:
        return self._pool
    
    def _exe(self, executor: Executor) -> Executor:
        return executor if executor is not None else self._pool
    
    async def get_cast_statistics(
        self, 
        story_id: str, 
        user_id: str,
        *,
        executor: Executor | None = None
    ) -> list[tuple[str, int, int]]:
        
        sql = f"""\
        SELECT
            pov,
            COUNT(*) AS scene_count,
            SUM(word_count) AS word_count
        FROM scene
        WHERE story_id=$1 AND user_id=$2
        GROUP BY pov
        ORDER BY scene_count DESC, word_count DESC
        """

        rows = await self._exe(executor).fetch(sql, story_id, user_id)

        return [(r["pov"], r["scene_count"], r["word_count"]) for r in rows]
    

    async def get_character_co_occurence_statistics(
        self,
        story_id: str,
        user_id: str,
        *,
        executor: Executor | None = None
    ) -> list[tuple[str, str, int, int]]:
        
        sql = f"""\
        SELECT
            sc.pov AS character_a,
            exploded.character_b AS character_b,
            COUNT(*) AS scene_count,
            SUM(word_count) AS word_count
        FROM "scene" sc
        CROSS JOIN LATERAL UNNEST(sc.mentioned_entities) AS exploded(character_b)
        WHERE 
            sc.story_id=$1 
            AND sc.user_id=$2
            AND sc.pov = ANY(sc.mentioned_entities)
            AND exploded.character_b != sc.pov
        GROUP BY character_a, character_b
        ORDER BY scene_count DESC, word_count DESC
        """

        rows = await self._exe(executor).fetch(sql, story_id, user_id)

        return [
            (r["character_a"], r["character_b"], r["scene_count"], r["word_count"])
            for r in rows
        ]
    
    async def get_character_statistics(
        self,
        story_id: str,
        user_id: str,
        *,
        executor: Executor | None = None
    ) -> list[tuple[str, int, str, int, int]]:
        
        sql = f"""\
        SELECT
            sc.chapter_id AS chapter_id,
            ARRAY_POSITION(s.path_array, sc.chapter_id) AS chapter_number,
            sc.pov AS character,
            COUNT(*) AS scene_count,
            SUM(sc.word_count) AS word_count
        FROM "scene" sc 
        INNER JOIN "story" s ON (sc.story_id = s.id)
        WHERE sc.story_id=$1 AND sc.user_id=$2
        GROUP BY chapter_id, chapter_number, character
        ORDER BY chapter_number
        """

        rows = await self._exe(executor).fetch(sql, story_id, user_id)

        return [
            (r["chapter_id"], r["chapter_number"], r["character"], r["scene_count"], r["word_count"])
            for r in rows
        ]

    async def get_scene_length_distribution(
        self,
        story_id: str,
        user_id: str,
        *,
        executor: Executor | None = None
    ) -> list[tuple[str, int]]:
        
        sql = f"""\
        SELECT
            (
                CASE
                    WHEN word_count <= 200 THEN '≤ 200'
                    WHEN word_count BETWEEN 201 AND 500 THEN '201-500'
                    WHEN word_count BETWEEN 501 AND 1000 THEN '501-1000'
                    WHEN word_count BETWEEN 1001 AND 2000 THEN '1001-2000'
                    WHEN word_count BETWEEN 2001 AND 4000 THEN '2001-4000'
                    ELSE '4000+'
                END
            ) AS scene_length,
            COUNT(*) AS scene_count
        FROM "scene"
        WHERE story_id=$1 AND user_id=$2
        GROUP BY scene_length
        """

        rows = await self._exe(executor).fetch(sql, story_id, user_id)

        return [
            (r["scene_length"], r["scene_count"])
            for r in rows
        ]

    async def get_tension_and_pacing_curves(
        self,
        story_id: str,
        user_id: str,
        *,
        executor: Executor | None = None
    ) -> list[tuple[str, int, float, float]]:

        sql = f"""\
        SELECT
            sc.chapter_id AS chapter_id,
            ARRAY_POSITION(s.path_array, sc.chapter_id) AS chapter_number,
            AVG(
                CASE
                    WHEN tension = 'low' THEN 1.0
                    WHEN tension = 'medium' THEN 2.0
                    WHEN tension = 'high' THEN 3.0
                END
            ) AS avg_tension,
            AVG(
                CASE
                    WHEN pacing = 'slow' THEN 1.0
                    WHEN pacing = 'steady' THEN 2.0
                    WHEN pacing = 'fast' THEN 3.0
                END
            ) AS avg_pacing
        FROM "scene" sc
        INNER JOIN "chapter" c ON (sc.chapter_id = c.id)
        INNER JOIN "story" s ON (sc.story_id = s.id)
        WHERE sc.story_id = $1 AND sc.user_id = $2
        GROUP BY chapter_id, chapter_number
        ORDER BY chapter_number
        """

        rows = await self._exe(executor).fetch(sql, story_id, user_id)

        return [
            (r["chapter_id"], r["chapter_number"], r["avg_tension"], r["avg_pacing"])
            for r in rows
        ]

    async def get_recent_chapters_rythm(
        self,
        story_id: str,
        user_id: str,
        k: int = 8,
        *,
        executor: Executor | None = None
    ) -> list[tuple[str, int, float, float]]:
        
        sql = f"""\
        SELECT
            sc.chapter_id AS chapter_id,
            ARRAY_POSITION(s.path_array, sc.chapter_id) AS chapter_number,
            AVG(
                CASE
                    WHEN tension = 'low' THEN 1.0
                    WHEN tension = 'medium' THEN 2.0
                    WHEN tension = 'high' THEN 3.0
                END
            ) AS avg_tension,
            AVG(
                CASE
                    WHEN pacing = 'slow' THEN 1.0
                    WHEN pacing = 'steady' THEN 2.0
                    WHEN pacing = 'fast' THEN 3.0
                END
            ) AS avg_pacing
        FROM "scene" sc
        INNER JOIN "chapter" c ON (sc.chapter_id = c.id)
        INNER JOIN "story" s ON (sc.story_id = s.id)
        WHERE sc.story_id = $1 AND sc.user_id = $2
        GROUP BY chapter_id, chapter_number
        ORDER BY chapter_number DESC
        LIMIT $3
        """

        rows = await self._exe(executor).fetch(sql, story_id, user_id, k)

        return [
            (r["chapter_id"], r["chapter_number"], r["avg_tension"], r["avg_pacing"])
            for r in rows
        ]

    async def get_entity_statistics(
        self,
        story_id: str,
        user_id: str,
        *,
        executor: Executor | None = None
    ) -> list[tuple[str, int, str]]:

        sql = """\
       WITH ranked AS (
            SELECT
                entity,
                description,
                ROW_NUMBER() OVER (PARTITION BY entity ORDER BY position ASC) AS rn
            FROM "scene", unnest(mentioned_entities) AS entity
            WHERE user_id = $1 AND story_id = $2
        )
        SELECT
            r.entity,
            COUNT(*) OVER (PARTITION BY r.entity) AS n,
            r.description AS sample_description
        FROM ranked r
        WHERE r.rn = 1
        ORDER BY n DESC, r.entity ASC
        """

        rows = await self._exe(executor).fetch(sql, user_id, story_id)

        return [
            (r["entity"], r["n"], r["sample_description"])
            for r in rows
        ]

