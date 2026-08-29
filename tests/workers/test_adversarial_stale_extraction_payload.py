from types import SimpleNamespace

import saq_worker


async def test_scene_job_never_extracts_stale_payload_over_newer_chapter_content(
    saq_context,
    fake_worker_services,
    job_ids,
) -> None:
    chapter_repo = fake_worker_services["chapter_repo"]
    extraction = fake_worker_services["extraction_service"]

    current_content = "CURRENT VERSION B"
    stale_queued_content = "STALE VERSION A"
    current = SimpleNamespace(
        id=job_ids["chapter_id"],
        story_id=job_ids["story_id"],
        user_id=job_ids["user_id"],
        content=current_content,
        published=True,
    )
    # The worker reads the chapter before and after extraction.
    chapter_repo.rows = [current, current]

    await saq_worker.scene_and_embedding_job(
        saq_context,
        chapter_id=job_ids["chapter_id"],
        story_id=job_ids["story_id"],
        user_id=job_ids["user_id"],
        content=stale_queued_content,
    )

    assert extraction.calls
    extracted_content = extraction.calls[0][2]
    assert extracted_content in (None, current_content), (
        "queued content is a stale snapshot: when a newer edit lands while the pending lock "
        "suppresses another job, the worker must extract canonical current content (or pass None "
        "so ExtractionService fetches it), never the stale payload captured at enqueue time"
    )
