from types import SimpleNamespace

import saq_worker


async def test_mid_job_edit_cannot_be_marked_current_with_stale_baseline(
    saq_context,
    fake_worker_services,
    fake_redis_client,
    job_ids,
) -> None:
    chapter_repo = fake_worker_services["chapter_repo"]

    before = SimpleNamespace(
        id=job_ids["chapter_id"],
        story_id=job_ids["story_id"],
        user_id=job_ids["user_id"],
        content="VERSION B",
        published=True,
    )
    after = SimpleNamespace(
        id=job_ids["chapter_id"],
        story_id=job_ids["story_id"],
        user_id=job_ids["user_id"],
        content="VERSION C edited while extraction was running",
        published=True,
    )
    chapter_repo.rows = [before, after]

    await saq_worker.scene_and_embedding_job(
        saq_context,
        chapter_id=job_ids["chapter_id"],
        story_id=job_ids["story_id"],
        user_id=job_ids["user_id"],
        content=before.content,
    )

    baseline_writes = [
        value
        for key, value in fake_redis_client.set_calls
        if key == f"chapter:baseline:{job_ids['chapter_id']}"
    ]

    assert before.content not in baseline_writes, (
        "if chapter content changes while extraction is running, stale extraction input must not "
        "be recorded as the current baseline; doing so falsely certifies derived state that no "
        "longer corresponds to canonical chapter content"
    )
