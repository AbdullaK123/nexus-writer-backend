"""UserRepository — raw asyncpg + SQL. Returns Pydantic UserRow."""
from __future__ import annotations
from typing import Tuple

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
    
    async def get_dashboard(
        self,
        *,
        user_id: str
    ) -> Tuple[dict, list[dict]]:
        
        async with self._pool.acquire() as conn:
        
            agg_sql = """
            WITH unique_dates AS (
                SELECT DISTINCT
                    DATE_TRUNC('day', updated_at)::date AS active_date
                FROM chapter
                WHERE user_id = $1
            ),
            numbered_dates AS (
                SELECT
                    active_date,
                    active_date - ROW_NUMBER() OVER(
                        ORDER BY active_date
                    ) * INTERVAL '1 day' AS streak_group
                FROM unique_dates
            ),
            all_streaks AS (
                SELECT
                    MAX(active_date) AS streak_end,
                    COUNT(*) AS streak_days
                FROM numbered_dates
                GROUP BY streak_group
            ),
            active_streak AS (
                SELECT 
                    COALESCE(MAX(streak_days), 0) AS current_streak_days
                FROM all_streaks
                WHERE streak_end >= CURRENT_DATE - INTERVAL '1 day'
            )
            SELECT
                SUM(c.word_count) AS total_words,
                COUNT(s.id) AS total_stories,
                COUNT(c.id) AS chapters_total,
                COUNT(CASE WHEN c.published THEN 1 ELSE 0 END) AS chapters_published,
                COUNT(sc.id) AS scenes_tracked,
                active_streak.current_streak_days AS streak_days
            FROM user u 
            WHERE u.id = $1
            INNER JOIN story s ON (u.id = s.user_id)
            INNER JOIN chapter c ON (u.id = c.user_id)
            INNER JOIN scene sc ON (u.id = sc.user_id)
            """

            agg_result = await conn.fetch(agg_sql, user_id)

            last_three_chapters_sql = """
            SELECT
                c.story_id AS story_id,
                c.id AS chapter_id,
                c.chapter_number AS chapter_number,
                c.word_count AS word_count,
                s.title AS story_title,
                c.title AS chapter_title,
                c.published AS published,
                c.updated_at AS updated_at
            FROM chapter c
            INNER JOIN story s ON (c.story_id = s.id)
            WHERE c.user_id = $1
            ORDER BY c.updated_at DESC
            LIMIT 3
            """

            last_three_chapters_result = await conn.fetch(last_three_chapters_sql, user_id)

    
            return dict(agg_result), [dict(result) for result in last_three_chapters_result]
