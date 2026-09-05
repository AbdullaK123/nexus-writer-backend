import asyncpg
from typing import Any, Literal
import secrets
import hashlib
from src.data.schemas.auth import AuthTokenRow
from src.data.schemas.enums import generate_uuid
from src.infrastructure.config.settings import config as app_config
from datetime import datetime, timezone as tz, timedelta

Executor = Any
Purpose = Literal['email_verification', 'password_reset']


class AuthTokenRepository:

    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    @property
    def pool(self) -> asyncpg.Pool:
        return self._pool

    def _exe(self, executor: Executor | None) -> Executor:
        return executor if executor is not None else self._pool

    @staticmethod
    def _hash(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    async def delete(
        self,
        *,
        user_id: str,
        token: str,
        purpose: Purpose,
        executor: Executor | None = None
    ) -> None:
        sql = """
        DELETE FROM "auth_tokens"
        WHERE user_id = $1 AND token_hash = $2 AND purpose = $3
        """
        await self._exe(executor).execute(
            sql,
            user_id,
            self._hash(token),
            purpose
        )

    async def get(
        self,
        *,
        token: str,
        purpose: Purpose,
        executor: Executor | None = None
    ) -> AuthTokenRow | None:
        sql = """
        SELECT *
        FROM "auth_tokens"
        WHERE token_hash = $1 AND purpose = $2
        """
        row = await self._exe(executor).fetchrow(
            sql,
            self._hash(token),
            purpose
        )
        return AuthTokenRow.model_validate(dict(row)) if row is not None else None

    async def consume(
        self,
        *,
        token: str,
        purpose: Purpose,
        executor: Executor | None = None,
    ) -> AuthTokenRow | None:
        """Atomically claim a bearer token exactly once."""
        sql = """
        DELETE FROM "auth_tokens"
        WHERE token_hash = $1 AND purpose = $2
        RETURNING *
        """
        row = await self._exe(executor).fetchrow(
            sql,
            self._hash(token),
            purpose,
        )
        return AuthTokenRow.model_validate(dict(row)) if row is not None else None

    async def create(
        self,
        *,
        user_id: str,
        purpose: Purpose,
        executor: Executor | None = None
    ) -> str:
        """Issue the one active token for this user/purpose.

        Re-issuing replaces the previous bearer credential atomically, so stale links
        become unusable instead of accumulating until TTL expiry.
        """
        token = secrets.token_urlsafe(32)
        sql = """
        INSERT INTO "auth_tokens" (id, user_id, token_hash, purpose, expires_at)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (user_id, purpose)
        DO UPDATE SET
            id = EXCLUDED.id,
            token_hash = EXCLUDED.token_hash,
            expires_at = EXCLUDED.expires_at,
            created_at = NOW()
        """
        await self._exe(executor).execute(
            sql,
            generate_uuid(),
            user_id,
            self._hash(token),
            purpose,
            datetime.now(tz.utc) + timedelta(minutes=app_config.auth.auth_token_ttl_mins)
        )
        return token
