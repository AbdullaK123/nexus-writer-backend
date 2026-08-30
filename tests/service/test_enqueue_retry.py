from __future__ import annotations

from typing import Any

import pytest
from tenacity import wait_none

from src.service.chapter.service import ChapterService
from src.service.utils.decorators import retry_enqueue


class FakeCache:
    def __init__(self) -> None:
        self.claimed: set[str] = set()
        self.deleted: list[str] = []

    async def set(self, key: str, value: str, **_: Any) -> bool:
        if key in self.claimed:
            return False
        self.claimed.add(key)
        return True

    async def delete(self, *keys: str) -> int:
        self.deleted.extend(keys)
        for key in keys:
            self.claimed.discard(key)
        return len(keys)


@pytest.mark.asyncio
async def test_retry_enqueue_exhaustion_raises_after_exactly_three_attempts() -> None:
    attempts = 0

    @retry_enqueue
    async def always_fail(**_: Any) -> None:
        nonlocal attempts
        attempts += 1
        raise ConnectionError("redis unavailable")

    always_fail.retry.wait = wait_none()

    with pytest.raises(ConnectionError, match="redis unavailable"):
        await always_fail()

    assert attempts == 3, "queue retries must be bounded or a Redis outage can pin request handlers indefinitely"


@pytest.mark.asyncio
async def test_exhausted_enqueue_releases_pending_claim_for_immediate_retry() -> None:
    cache = FakeCache()
    service = object.__new__(ChapterService)
    service._cache = cache
    attempts = 0

    @retry_enqueue
    async def always_fail(**_: Any) -> None:
        nonlocal attempts
        attempts += 1
        raise ConnectionError("redis unavailable")

    always_fail.retry.wait = wait_none()
    service._enqueue_extraction_job = always_fail

    chapter_id = "chapter-1"
    story_id = "story-1"
    user_id = "user-1"
    pending_key = f"chapter:extraction-pending:{chapter_id}"

    with pytest.raises(ConnectionError, match="redis unavailable"):
        await service.queue_extraction_job(
            chapter_id=chapter_id,
            story_id=story_id,
            user_id=user_id,
            content="chapter text",
        )

    assert attempts == 3
    assert pending_key not in cache.claimed, (
        "an exhausted enqueue must release the pending key; otherwise no job exists but the chapter is blocked until the 30-minute TTL expires"
    )
    assert pending_key in cache.deleted

    claimed_again = await cache.set(pending_key, "1", nx=True, ex=1800)
    assert claimed_again is True, (
        "after enqueue failure the next request must be able to reclaim work immediately instead of inheriting a ghost lock"
    )
