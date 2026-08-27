from datetime import datetime, timedelta, timezone

from src.data.repositories.session import SessionRepository
from src.data.schemas.auth import SessionRow, UserRow


async def test_create_and_get_session_preserve_binding_and_connection_metadata(
    session_repo: SessionRepository,
    repo_user: UserRow,
) -> None:
    expires_at = datetime.now(timezone.utc) + timedelta(hours=2)

    created = await session_repo.create(
        session_id="session-a",
        user_id=repo_user.id,
        expires_at=expires_at,
        ip_address="10.0.0.1",
        user_agent="integration-test",
    )
    resolved = await session_repo.get("session-a")

    assert resolved is not None
    assert resolved.session_id == created.session_id
    assert resolved.user_id == repo_user.id
    assert resolved.ip_address == "10.0.0.1"
    assert resolved.user_agent == "integration-test"
    assert resolved.expires_at == expires_at


async def test_missing_session_returns_none(session_repo: SessionRepository) -> None:
    assert await session_repo.get("missing-session") is None


async def test_delete_revokes_session(
    session_repo: SessionRepository,
    valid_session: SessionRow,
) -> None:
    assert await session_repo.delete(valid_session.session_id) is True
    assert await session_repo.get(valid_session.session_id) is None
    assert await session_repo.delete(valid_session.session_id) is False


async def test_multiple_sessions_for_same_user_are_independent(
    session_repo: SessionRepository,
    repo_user: UserRow,
) -> None:
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    first = await session_repo.create(
        session_id="session-one",
        user_id=repo_user.id,
        expires_at=expires_at,
        ip_address=None,
        user_agent=None,
    )
    second = await session_repo.create(
        session_id="session-two",
        user_id=repo_user.id,
        expires_at=expires_at,
        ip_address=None,
        user_agent=None,
    )

    await session_repo.delete(first.session_id)

    assert await session_repo.get(first.session_id) is None
    surviving = await session_repo.get(second.session_id)
    assert surviving is not None
    assert surviving.user_id == repo_user.id


async def test_expired_session_remains_addressable_until_cleanup(
    session_repo: SessionRepository,
    expired_session: SessionRow,
) -> None:
    resolved = await session_repo.get(expired_session.session_id)

    assert resolved is not None
    assert resolved.expires_at < datetime.now(timezone.utc)


async def test_cleanup_expired_removes_only_expired_sessions(
    session_repo: SessionRepository,
    valid_session: SessionRow,
    expired_session: SessionRow,
) -> None:
    deleted = await session_repo.delete_expired()

    assert deleted == 1
    assert await session_repo.get(expired_session.session_id) is None
    assert await session_repo.get(valid_session.session_id) is not None


async def test_session_is_bound_to_correct_user(
    session_repo: SessionRepository,
    repo_user: UserRow,
    repo_other_user: UserRow,
) -> None:
    first = await session_repo.create(
        session_id="user-a-session",
        user_id=repo_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ip_address=None,
        user_agent=None,
    )
    second = await session_repo.create(
        session_id="user-b-session",
        user_id=repo_other_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ip_address=None,
        user_agent=None,
    )

    resolved_first = await session_repo.get(first.session_id)
    resolved_second = await session_repo.get(second.session_id)

    assert resolved_first is not None
    assert resolved_second is not None
    assert resolved_first.user_id == repo_user.id
    assert resolved_second.user_id == repo_other_user.id
