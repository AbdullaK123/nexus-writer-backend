from datetime import timedelta
from typing import Literal
from uuid_extensions import uuid7str

from src.data.schemas.auth import AuthTokenRow

from .common import now

Purpose = Literal["email_verification", "password_reset"]


class FakeAuthTokenRepository:
    def __init__(self) -> None:
        self._tokens: dict[str, AuthTokenRow] = {}
        self.error: Exception | None = None

    async def create(self, *, user_id: str, purpose: Purpose, executor=None) -> str:
        if self.error:
            raise self.error
        stale = [
            token
            for token, row in self._tokens.items()
            if row.user_id == user_id and row.purpose == purpose
        ]
        for token in stale:
            del self._tokens[token]

        token = f"token-{uuid7str()}"
        self._tokens[token] = AuthTokenRow(
            id=uuid7str(),
            user_id=user_id,
            token_hash="fake-hash",
            purpose=purpose,
            expires_at=now() + timedelta(minutes=15),
            created_at=now(),
        )
        return token

    async def get(self, *, token: str, purpose: Purpose, executor=None) -> AuthTokenRow | None:
        if self.error:
            raise self.error
        row = self._tokens.get(token)
        if row is None or row.purpose != purpose:
            return None
        return row

    async def consume(self, *, token: str, purpose: Purpose, executor=None) -> AuthTokenRow | None:
        if self.error:
            raise self.error
        row = self._tokens.get(token)
        if row is None or row.purpose != purpose:
            return None
        del self._tokens[token]
        return row

    async def delete(
        self,
        *,
        user_id: str,
        token: str,
        purpose: Purpose,
        executor=None,
    ) -> None:
        if self.error:
            raise self.error
        row = self._tokens.get(token)
        if row is not None and row.user_id == user_id and row.purpose == purpose:
            del self._tokens[token]
