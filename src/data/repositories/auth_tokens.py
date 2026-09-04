import asyncpg
from typing import Any, Literal
import secrets
import hashlib
from src.data.schemas.auth import AuthTokenRow
from src.data.schemas.enums import generate_uuid
from src.infrastructure.config.settings import config as app_config
from datetime import datetime, timezone as tz, timedelta

Executor = Any

class AuthTokenRepository:

    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    @property
    def pool(self) -> asyncpg.Pool:
        return self._pool

    def _exe(self, executor: Executor | None) -> Executor:
        return executor if executor is not None else self._pool


    async def delete(
        self,
        *,
        id: str,
        user_id: str,
        executor: Executor | None = None
    ) -> None:
        sql = """
        DELETE FROM "auth_tokens" 
        WHERE user_id = $1 AND token_hash = $2 AND purpose = $3
        """
        await self._exe(executor).execute(
            sql,
            id,
            user_id
        )


    async def get(
        self,
        *,
        user_id: str,
        token: str,
        purpose: Literal['email_verification', 'password_reset'],
        executor: Executor | None = None
    ) -> AuthTokenRow | None:

        sql = """
        SELECT *
        FROM "auth_tokens"
        WHERE user_id = $1 AND token_hash = $2 AND purpose = $3
        """

        row = await self._exe(executor).fetchrow(
            sql,
            user_id,
            hashlib.sha256(token.encode()).hexdigest(),
            purpose
        )

        return AuthTokenRow.model_validate(dict(row)) if row is not None else None


    async def create(
        self,
        *,
        user_id: str,
        purpose: Literal['email_verification', 'password_reset'],
        executor: Executor | None = None
    ) -> str:

        token = secrets.token_urlsafe(32)

        sql = """
        INSERT INTO "auth_tokens" (id, user_id, token_hash, purpose, expires_at)
        VALUES ($1, $2, $3, $4, $5)
        """

        await self._exe(executor).execute(
            sql,
            generate_uuid(),
            user_id,
            hashlib.sha256(token.encode()).hexdigest(),
            purpose,
            datetime.now(tz.utc) + timedelta(minutes=app_config.auth.auth_token_ttl_mins)
        )

        return token