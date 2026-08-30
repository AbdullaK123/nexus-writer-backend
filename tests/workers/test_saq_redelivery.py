from __future__ import annotations

from typing import Any

import pytest

import saq_worker
from tests.workers.mocks import PublishedChapter


@pytest.mark.asyncio
async def test_completed_scene_job_redelivery_is_a_noop(
    saq_context: dict[str, Any],
    job_ids: dict[str, str],
    fake_worker_services: dict[str, Any],
    fake_redis_client: Any,
) -> None:
    chapter_repo = fake_worker_services["chapter_repo"]
    chapter_repo.rows = [
        PublishedChapter(job_ids["chapter_id"], job_ids["story_id"]),
        PublishedChapter(job_ids["chapter_id"], job_ids["story_id"]),
        PublishedChapter(job_ids["chapter_id"], job_ids["story_id"]),
    ]

    await saq_worker.scene_and_embedding_job(saq_context, **job_ids)
    await saq_worker.scene_and_embedding_job(saq_context, **job_ids)

    assert len(fake_worker_services["extraction_service"].calls) == 1, (
        "redelivery of an already-completed chapter version must not repeat extraction and risk duplicating derived rows"
    )
    assert len(fake_worker_services["embedding_service"].calls) == 1
    assert len(fake_worker_services["chapter_service"].comment_calls) == 1
    assert len(fake_worker_services["pubsub"].published) == 3, (
        "a fully completed redelivery must not emit duplicate success notifications"
    )
    assert any(
        key.startswith(f"chapter:extraction-complete:{job_ids['chapter_id']}:")
        for key, _ in fake_redis_client.set_calls
    )


@pytest.mark.asyncio
async def test_failed_scene_job_does_not_mark_version_complete(
    saq_context: dict[str, Any],
    job_ids: dict[str, str],
    fake_worker_services: dict[str, Any],
    fake_redis_client: Any,
) -> None:
    chapter_repo = fake_worker_services["chapter_repo"]
    chapter_repo.rows = [
        PublishedChapter(job_ids["chapter_id"], job_ids["story_id"]),
        PublishedChapter(job_ids["chapter_id"], job_ids["story_id"]),
        PublishedChapter(job_ids["chapter_id"], job_ids["story_id"]),
    ]
    extraction = fake_worker_services["extraction_service"]
    extraction.error = RuntimeError("provider failed")

    with pytest.raises(RuntimeError, match="provider failed"):
        await saq_worker.scene_and_embedding_job(saq_context, **job_ids)

    assert not any(
        key.startswith(f"chapter:extraction-complete:{job_ids['chapter_id']}:")
        for key, _ in fake_redis_client.set_calls
    ), "a partial failure must never poison the completion marker and suppress the queue's legitimate retry"

    extraction.error = None
    await saq_worker.scene_and_embedding_job(saq_context, **job_ids)

    assert len(extraction.calls) == 2, (
        "an at-least-once retry after partial failure must execute again because the previous attempt never completed"
    )
    assert any(
        key.startswith(f"chapter:extraction-complete:{job_ids['chapter_id']}:")
        for key, _ in fake_redis_client.set_calls
    )
