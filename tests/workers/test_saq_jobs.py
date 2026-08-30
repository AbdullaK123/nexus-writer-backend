from __future__ import annotations

from typing import Any

import pytest

import saq_worker
from tests.workers.mocks import PublishedChapter


async def test_job_ids_are_validated_before_work(
    saq_context: dict[str, Any],
    job_ids: dict[str, str],
    fake_worker_services: dict[str, Any],
) -> None:
    with pytest.raises(ValueError, match="Invalid chapter_id"):
        await saq_worker.scene_and_embedding_job(
            saq_context,
            chapter_id="not-a-uuid",
            story_id=job_ids["story_id"],
            user_id=job_ids["user_id"],
        )

    assert fake_worker_services["chapter_repo"].get_calls == []
    assert fake_worker_services["extraction_service"].calls == []


async def test_scene_job_runs_extraction_embedding_analysis_and_notifications(
    saq_context: dict[str, Any],
    job_ids: dict[str, str],
    fake_worker_services: dict[str, Any],
    fake_redis_client: Any,
) -> None:
    chapter_repo = fake_worker_services["chapter_repo"]
    chapter_repo.rows = [
        PublishedChapter(job_ids["chapter_id"], job_ids["story_id"]),
        PublishedChapter(job_ids["chapter_id"], job_ids["story_id"]),
    ]

    await saq_worker.scene_and_embedding_job(
        saq_context,
        **job_ids,
        content="chapter text",
    )

    assert fake_worker_services["extraction_service"].calls == [
        (job_ids["chapter_id"], job_ids["user_id"], "chapter text")
    ]
    assert fake_worker_services["embedding_service"].calls == [job_ids["chapter_id"]]
    assert len(fake_worker_services["story_service"].pulse_calls) == 1
    assert {name for name, _ in fake_worker_services["analytics_service"].calls} == {
        "plot",
        "acts",
        "contradictions",
        "entities",
    }
    assert len(fake_worker_services["chapter_service"].summary_calls) == 1
    assert len(fake_worker_services["chapter_service"].comment_calls) == 1
    assert [message.kind for _, message in fake_worker_services["pubsub"].published] == [
        "scenes_extracted",
        "analysis_ready",
        "comments_ready",
    ]
    assert (
        f"chapter:baseline:{job_ids['chapter_id']}",
        "chapter text",
    ) in fake_redis_client.set_calls
    assert any(
        key.startswith(f"chapter:extraction-complete:{job_ids['chapter_id']}:")
        for key, _ in fake_redis_client.set_calls
    )
    assert f"chapter:extraction-pending:{job_ids['chapter_id']}" in fake_redis_client.delete_calls


async def test_scene_job_skips_unpublished_chapter(
    saq_context: dict[str, Any],
    job_ids: dict[str, str],
    fake_worker_services: dict[str, Any],
    fake_redis_client: Any,
) -> None:
    fake_worker_services["chapter_repo"].rows = [
        PublishedChapter(
            job_ids["chapter_id"],
            job_ids["story_id"],
            published=False,
        )
    ]

    await saq_worker.scene_and_embedding_job(saq_context, **job_ids)

    assert fake_worker_services["extraction_service"].calls == []
    assert fake_worker_services["embedding_service"].calls == []
    assert fake_worker_services["pubsub"].published == []
    assert fake_redis_client.delete_calls == [
        f"chapter:extraction-pending:{job_ids['chapter_id']}"
    ]


async def test_scene_job_failure_re_raises_and_cleans_pending_state(
    saq_context: dict[str, Any],
    job_ids: dict[str, str],
    fake_worker_services: dict[str, Any],
    fake_redis_client: Any,
) -> None:
    fake_worker_services["chapter_repo"].rows = [
        PublishedChapter(job_ids["chapter_id"], job_ids["story_id"])
    ]
    fake_worker_services["extraction_service"].error = RuntimeError("provider failed")

    with pytest.raises(RuntimeError, match="provider failed"):
        await saq_worker.scene_and_embedding_job(saq_context, **job_ids)

    assert fake_worker_services["pubsub"].published[-1][1].kind == "job_failed"
    assert f"chapter:extraction-pending:{job_ids['chapter_id']}" in fake_redis_client.delete_calls


async def test_chapter_reanalysis_calls_expected_services(
    saq_context: dict[str, Any],
    job_ids: dict[str, str],
    fake_worker_services: dict[str, Any],
) -> None:
    fake_worker_services["chapter_repo"].rows = [
        PublishedChapter(job_ids["chapter_id"], job_ids["story_id"])
    ]

    await saq_worker.chapter_reanalysis_job(saq_context, **job_ids)

    assert len(fake_worker_services["chapter_service"].summary_calls) == 1
    assert len(fake_worker_services["chapter_service"].comment_calls) == 1
    assert fake_worker_services["pubsub"].published[-1][1].kind == "comments_ready"


async def test_story_reanalysis_refreshes_all_story_analysis(
    saq_context: dict[str, Any],
    job_ids: dict[str, str],
    fake_worker_services: dict[str, Any],
    fake_redis_client: Any,
) -> None:
    await saq_worker.story_reanalysis_job(
        saq_context,
        story_id=job_ids["story_id"],
        user_id=job_ids["user_id"],
        story_title="Test Story",
    )

    assert len(fake_worker_services["story_service"].pulse_calls) == 1
    assert len(fake_worker_services["analytics_service"].calls) == 4
    assert fake_worker_services["pubsub"].published[-1][1].kind == "analysis_ready"
    assert fake_redis_client.delete_calls == [
        f"story:reanalysis-pending:{job_ids['story_id']}"
    ]


async def test_story_reanalysis_failure_is_reported_and_re_raised(
    saq_context: dict[str, Any],
    job_ids: dict[str, str],
    fake_worker_services: dict[str, Any],
) -> None:
    fake_worker_services["story_service"].error = RuntimeError("analysis failed")

    with pytest.raises(RuntimeError, match="analysis failed"):
        await saq_worker.story_reanalysis_job(
            saq_context,
            story_id=job_ids["story_id"],
            user_id=job_ids["user_id"],
            story_title="Test Story",
        )

    assert fake_worker_services["pubsub"].published[-1][1].kind == "job_failed"
