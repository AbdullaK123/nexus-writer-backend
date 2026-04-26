"""Tests for src/service/jobs/session.py — cleanup_expired_sessions_batched.

Happy-path assumption: the loop terminates correctly, deletes only expired
rows, batches by `batch_size`, and only logs when something was deleted.
"""
from datetime import datetime, timedelta, timezone

import pytest
from loguru import logger

from src.data.models import Session
from src.service.jobs.session import cleanup_expired_sessions_batched
from tests.factories import make_user


async def _make_session(user, *, sid: str, expires_at: datetime):
    return await Session.create(
        session_id=sid, user_id=user.id, expires_at=expires_at,
    )


class TestCleanupExpiredSessionsBatched:
    async def test_terminates_when_no_sessions_exist(self, mocker):
        # Assumption: the while-loop exits cleanly on an empty table
        spy = mocker.spy(logger, "info")
        await cleanup_expired_sessions_batched(batch_size=10)
        # No work => no completion log
        assert not any("session.cleanup_complete" in str(c)
                       for c in spy.call_args_list)

    async def test_does_not_delete_unexpired_sessions(self):
        # Assumption: filter is strictly `expires_at < now`
        user = await make_user()
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        await _make_session(user, sid="alive", expires_at=future)

        await cleanup_expired_sessions_batched(batch_size=10)

        assert await Session.filter(session_id="alive").exists()

    async def test_deletes_all_expired_sessions_in_one_batch(self):
        user = await make_user()
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        for i in range(3):
            await _make_session(user, sid=f"dead-{i}", expires_at=past)

        await cleanup_expired_sessions_batched(batch_size=10)

        assert await Session.filter(session_id__startswith="dead-").count() == 0

    async def test_iterates_multiple_batches_when_more_rows_than_batch_size(self):
        # Assumption: loop continues while a full batch is returned
        user = await make_user()
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        for i in range(5):
            await _make_session(user, sid=f"e-{i}", expires_at=past)

        await cleanup_expired_sessions_batched(batch_size=2)

        # Final state: every expired row removed across batches
        assert await Session.filter(expires_at__lt=datetime.now(timezone.utc)).count() == 0

    async def test_terminates_when_short_batch_returned(self, mocker):
        # Assumption: the early-exit branch (len(expired) < batch_size) prevents
        # an extra empty round trip after the last batch.
        user = await make_user()
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        await _make_session(user, sid="only-one", expires_at=past)

        # Spy on Session.filter to count invocations
        original = Session.filter
        call_count = {"n": 0}

        def counting_filter(*args, **kwargs):
            call_count["n"] += 1
            return original(*args, **kwargs)

        mocker.patch.object(Session, "filter", side_effect=counting_filter)

        await cleanup_expired_sessions_batched(batch_size=10)

        # 1 SELECT (returned 1 row, < batch_size) + 1 DELETE = 2 calls
        # No second SELECT because the short-batch early-exit triggers
        assert call_count["n"] == 2

    async def test_logs_completion_only_when_total_deleted_gt_zero(self, mocker):
        user = await make_user()
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        await _make_session(user, sid="x", expires_at=past)

        spy = mocker.spy(logger, "info")

        await cleanup_expired_sessions_batched(batch_size=10)

        assert any("session.cleanup_complete" in str(c.args)
                   for c in spy.call_args_list)
