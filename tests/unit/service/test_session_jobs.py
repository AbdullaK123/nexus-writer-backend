"""Tests for src/service/jobs/session.py — cleanup_expired_sessions.

Happy-path assumption: cleanup deletes only expired rows and only logs when
something was deleted.
"""
from datetime import datetime, timedelta, timezone

from loguru import logger

from src.data.models import Session
from src.service.jobs.session import cleanup_expired_sessions
from tests.factories import make_user


async def _make_session(user, *, sid: str, expires_at: datetime):
    return await Session.create(
        session_id=sid, user_id=user.id, expires_at=expires_at,
    )


class TestCleanupExpiredSessions:
    async def test_terminates_when_no_sessions_exist(self, mocker):
        spy = mocker.spy(logger, "info")
        await cleanup_expired_sessions()
        # No work => no completion log
        assert not any("session.cleanup_complete" in str(c)
                       for c in spy.call_args_list)

    async def test_does_not_delete_unexpired_sessions(self):
        # Assumption: filter is strictly `expires_at < now`
        user = await make_user()
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        await _make_session(user, sid="alive", expires_at=future)

        await cleanup_expired_sessions()

        assert await Session.filter(session_id="alive").exists()

    async def test_deletes_all_expired_sessions(self):
        user = await make_user()
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        for i in range(3):
            await _make_session(user, sid=f"dead-{i}", expires_at=past)

        await cleanup_expired_sessions()

        assert await Session.filter(session_id__startswith="dead-").count() == 0

    async def test_logs_completion_only_when_total_deleted_gt_zero(self, mocker):
        user = await make_user()
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        await _make_session(user, sid="x", expires_at=past)

        spy = mocker.spy(logger, "info")

        await cleanup_expired_sessions()

        assert any("session.cleanup_complete" in str(c.args)
                   for c in spy.call_args_list)
