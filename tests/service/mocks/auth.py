from datetime import datetime
from uuid_extensions import uuid7str

from src.data.schemas.auth import SessionRow, UserRow

from .common import now


class FakeUserRepository:
    def __init__(self):
        self._users: dict[str, UserRow] = {}
        self._by_email: dict[str, str] = {}
        self.error: Exception | None = None
        self.create_error: Exception | None = None

    def seed(self, user: UserRow) -> None:
        self._users[user.id] = user
        self._by_email[user.email] = user.id

    def remove(self, user_id: str) -> None:
        user = self._users.pop(user_id, None)
        if user is not None:
            self._by_email.pop(user.email, None)

    async def get_by_id(self, user_id: str, executor=None) -> UserRow | None:
        if self.error:
            raise self.error
        return self._users.get(user_id)

    async def get_by_email(self, email: str, executor=None) -> UserRow | None:
        if self.error:
            raise self.error
        uid = self._by_email.get(email)
        return self._users.get(uid) if uid else None

    async def create(
        self,
        *,
        username: str,
        email: str,
        password_hash: str | None,
        profile_img: str | None,
        verified: bool = False,
        executor=None,
    ) -> UserRow:
        if self.create_error:
            raise self.create_error
        if self.error:
            raise self.error
        user = UserRow(
            id=uuid7str(),
            username=username,
            email=email,
            password_hash=password_hash,
            profile_img=profile_img,
            settings={},
            created_at=now(),
            updated_at=now(),
            email_verified=verified,
        )
        self.seed(user)
        return user

    async def verify_user(self, user_id: str, executor=None) -> None:
        user = self._users.get(user_id)
        if user is not None:
            self._users[user_id] = user.model_copy(update={"email_verified": True})

    async def update_password(self, user_id: str, password_hash: str, executor=None) -> None:
        user = self._users.get(user_id)
        if user is not None:
            self._users[user_id] = user.model_copy(update={"password_hash": password_hash})

    async def update_settings(self, user_id: str, update: dict) -> UserRow | None:
        if self.error:
            raise self.error
        user = self._users.get(user_id)
        if not user:
            return None
        merged = {**user.settings, **update}
        updated = user.model_copy(update={"settings": merged, "updated_at": now()})
        self._users[user_id] = updated
        return updated

    async def get_dashboard(self, *, user_id: str) -> tuple[dict, list[dict]]:
        if self.error:
            raise self.error
        return {}, []

    async def get_editor_link_params(self, *, user_id: str) -> list[tuple]:
        if self.error:
            raise self.error
        return []

    async def get_chat_link_params(self, *, user_id: str) -> list[tuple]:
        if self.error:
            raise self.error
        return []


class FakeSessionRepository:
    def __init__(self):
        self._sessions: dict[str, SessionRow] = {}
        self.error: Exception | None = None
        self.create_error: Exception | None = None

    def seed(self, session: SessionRow) -> None:
        self._sessions[session.session_id] = session

    async def get(self, session_id: str, executor=None) -> SessionRow | None:
        if self.error:
            raise self.error
        return self._sessions.get(session_id)

    async def create(
        self,
        *,
        user_id: str,
        session_id: str,
        expires_at: datetime,
        ip_address: str | None = None,
        user_agent: str | None = None,
        executor=None,
    ) -> SessionRow:
        if self.create_error:
            raise self.create_error
        if self.error:
            raise self.error
        session = SessionRow(
            session_id=session_id,
            user_id=user_id,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=now(),
            updated_at=now(),
        )
        self.seed(session)
        return session

    async def delete(self, session_id: str, executor=None) -> bool:
        if self.error:
            raise self.error
        return self._sessions.pop(session_id, None) is not None

    async def delete_all(self, user_id: str, executor=None) -> bool:
        if self.error:
            raise self.error
        keys = [key for key, value in self._sessions.items() if value.user_id == user_id]
        for key in keys:
            del self._sessions[key]
        return bool(keys)

    async def delete_expired(self, executor=None) -> int:
        if self.error:
            raise self.error
        current = now()
        expired = [key for key, value in self._sessions.items() if value.expires_at < current]
        for key in expired:
            del self._sessions[key]
        return len(expired)
