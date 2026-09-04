"""UserRepository — raw asyncpg + SQL. Returns Pydantic UserRow."""

from __future__ import annotations
from typing import Any, List, Tuple

import asyncpg
import json
from src.data.schemas import UserRow
from src.data.schemas.auth import OAuthUserRow
from src.data.schemas.enums import generate_uuid
from src.infrastructure.auth.password import hash_password


_USER_COLUMNS = """
    id, username, email, password_hash, profile_img, email_verified, settings,
    created_at, updated_at
"""

Executor = Any

class UserRepository:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    @property
    def pool(self) -> asyncpg.Pool:
        return self._pool

    def _exe(self, executor: Executor) -> Executor:
        return executor if executor is not None else self._pool

    async def get_by_id(self, user_id: str) -> UserRow | None:
        sql = f'SELECT {_USER_COLUMNS} FROM "user" WHERE id = $1'
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(sql, user_id)
        return UserRow.model_validate(dict(row)) if row else None

    async def get_by_email(
        self,
        email: str,
        executor: Executor | None = None,
    ) -> UserRow | None:
        sql = f'SELECT {_USER_COLUMNS} FROM "user" WHERE email = $1'
        row = await self._exe(executor).fetchrow(sql, email)
        return UserRow.model_validate(dict(row)) if row else None


    async def verify_user(
        self,
        user_id: str,
        executor: Executor | None = None,
    ) -> None:
        sql = """
        UPDATE "user"
        SET email_verified = True
        WHERE id = $1
        AND email_verified = False;
        """
        await self._exe(executor).execute(sql, user_id)


    async def update_password(
        self,
        user_id: str,
        password_hash: str,
        executor: Executor | None = None,
    ) -> None:
        sql = """
        UPDATE "user"
        SET password_hash = $1
        WHERE id = $2
        """
        await self._exe(executor).execute(sql, password_hash, user_id)


    async def update_settings(self, user_id: str, update: dict) -> UserRow | None:

        sql = f"""\
        UPDATE "user"
        SET settings = settings || $2::JSONB
        WHERE id = $1
        RETURNING {_USER_COLUMNS}
        """

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(sql, user_id, update)

        return UserRow.model_validate(dict(row)) if row else None

    async def create(
        self,
        *,
        username: str,
        email: str,
        password_hash: str | None,
        profile_img: str | None,
        verified: bool = False,
        executor: Executor | None = None
    ) -> UserRow:
        sql = f"""
            INSERT INTO "user"
                (id, username, email, password_hash, profile_img,
                 created_at, updated_at, email_verified)
            VALUES ($1, $2, $3, $4, $5, NOW(), NOW(), $6)
            RETURNING {_USER_COLUMNS}
        """
        row = await self._exe(executor).fetchrow(
            sql,
            generate_uuid(),
            username,
            email,
            password_hash,
            profile_img,
            verified
        )
        assert row is not None
        return UserRow.model_validate(dict(row))
    

    async def create_oauth(
        self,
        *,
        user_id: str,
        provider: str,
        provider_user_id: str,
        executor: Executor | None = None
    ) -> OAuthUserRow:

        sql = """
        INSERT INTO "oauth_accounts"
            (id, user_id, provider, provider_user_id)
        VALUES ($1, $2, $3, $4)
        RETURNING *
        """
        row = await self._exe(executor).fetchrow(
            sql,
            generate_uuid(),
            user_id,
            provider,
            provider_user_id
        )
        assert row is not None
        return OAuthUserRow.model_validate(dict(row))

    async def get_oauth_account(
        self,
        *,
        provider: str,
        provider_user_id: str,
        executor: Executor | None = None,
    ) -> OAuthUserRow | None:

        sql = """
        SELECT
            id,
            user_id,
            provider,
            provider_user_id
        FROM "oauth_accounts"
        WHERE provider=$1 AND provider_user_id=$2
        """

        row = await self._exe(executor).fetchrow(sql, provider, provider_user_id)

        return OAuthUserRow.model_validate(dict(row)) if row is not None else None



    async def get_dashboard(self, *, user_id: str) -> Tuple[dict, list[dict]]:
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
                    active_date - (ROW_NUMBER() OVER (ORDER BY active_date) * INTERVAL '1 day') AS streak_group
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
            ),
            user_metrics AS (
                SELECT
                    $1 AS user_id,
                    COALESCE((SELECT COUNT(*) FROM story WHERE user_id = $1), 0) AS total_stories,
                    COALESCE((SELECT COUNT(*) FROM scene WHERE user_id = $1), 0) AS scenes_tracked,
                    COALESCE((SELECT COUNT(*) FROM chapter WHERE user_id = $1), 0) AS chapters_total,
                    COALESCE((SELECT COUNT(*) FROM chapter WHERE user_id = $1 AND published = true), 0) AS chapters_published,
                    COALESCE((SELECT SUM(word_count) FROM chapter WHERE user_id = $1), 0) AS raw_word_count
            )
            SELECT
                m.raw_word_count AS total_words,
                m.total_stories,
                m.chapters_total,
                m.chapters_published,
                m.scenes_tracked,
                a.current_streak_days AS streak_days
            FROM user_metrics m
            CROSS JOIN active_streak a;
            """

            agg_result = await conn.fetchrow(agg_sql, user_id)

            last_three_chapters_sql = """
            SELECT
                c.story_id AS story_id,
                c.id AS chapter_id,
                ARRAY_POSITION(s.path_array, c.id) AS chapter_number,
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

            last_three_chapters_result = await conn.fetch(
                last_three_chapters_sql, user_id
            )

            return (dict(agg_result) if agg_result else {}), [
                dict(result) for result in last_three_chapters_result
            ]

    async def get_editor_link_params(self, *, user_id: str) -> List[Tuple[str, str, int, str]]:

        sql = """\
        SELECT
            s.id AS story_id,
            c.id AS chapter_id,
            ARRAY_POSITION(s.path_array, c.id) AS chapter_number,
            CONCAT(
                s.title, 
                ' - ',
                'Chapter ',
                ARRAY_POSITION(s.path_array, c.id)::TEXT,
                ' ( ',
                c.title,
                ' )'
            ) AS label
        FROM "story" s
        INNER JOIN "chapter" c ON (s.id = c.story_id)
        WHERE s.user_id = $1
        """

        async with self._pool.acquire() as conn:

            result = await conn.fetch(sql, user_id)

        return [
            (r['story_id'], r['chapter_id'], r['chapter_number'], r['label'])
            for r in result
        ]

    async def get_chat_link_params(self, *, user_id: str) -> List[Tuple[str, str]]:
    
        sql = """\
        SELECT
            s.id AS story_id,
            s.title AS title
        FROM "story" s
        WHERE s.user_id = $1
        """
    
        async with self._pool.acquire() as conn:
            result = await conn.fetch(sql, user_id)
    
        return [
            (r['story_id'], r['title'])
            for r in result
        ]