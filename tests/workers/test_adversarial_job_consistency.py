from types import SimpleNamespace

import pytest

import saq_worker


async def test_scene_job_rejects_story_chapter_mismatch_before_side_effects(
    saq_context,
    fake_worker_services,
    fake_redis_client,
    job_ids,
) -> None:
    chapter_repo = fake_worker_services["chapter_repo"]
    extraction = fake_worker_services["extraction_service"]
    embedding = fake_worker_services["embedding_service"]
    story_service = fake_worker_services["story_service"]
    analytics = fake_worker_services["analytics_service"]
    pubsub = fake_worker_services["pubsub"]

    chapter_repo.rows = [
        SimpleNamespace(
            id=job_ids["chapter_id"],
            story_id="44444444-4444-4444-8444-444444444444",
            published=True,
        )
    ]

    with pytest.raises(ValueError, match="story"):
        await saq_worker.scene_and_embedding_job(
            saq_context,
            chapter_id=job_ids["chapter_id"],
            story_id=job_ids["story_id"],
            user_id=job_ids["user_id"],
            content="author text",
        )

    assert extraction.calls == []
    assert embedding.calls == []
    assert story_service.pulse_calls == []
    assert analytics.calls == []
    assert pubsub.published == []
    assert fake_redis_client.set_calls == []


async def test_chapter_reanalysis_rejects_story_chapter_mismatch_before_analysis(
    saq_context,
    fake_worker_services,
    job_ids,
) -> None:
    chapter_repo = fake_worker_services["chapter_repo"]
    chapter_service = fake_worker_services["chapter_service"]
    pubsub = fake_worker_services["pubsub"]

    chapter_repo.rows = [
        SimpleNamespace(
            id=job_ids["chapter_id"],
            story_id="44444444-4444-4444-8444-444444444444",
            published=True,
        )
    ]

    with pytest.raises(ValueError, match="story"):
        await saq_worker.chapter_reanalysis_job(
            saq_context,
            chapter_id=job_ids["chapter_id"],
            story_id=job_ids["story_id"],
            user_id=job_ids["user_id"],
        )

    assert chapter_service.summary_calls == []
    assert chapter_service.comment_calls == []
    assert pubsub.published == []
