import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from src.data.schemas.chapter import ChapterRow
from src.data.schemas.scene import Scene, SceneExtraction, SceneRow
from src.infrastructure.config import config
from src.infrastructure.exceptions import DatabaseError, LLMServiceError
from src.service.exceptions import InternalError, NotFoundError
from src.service.extraction import service as extraction_module
from src.service.extraction.service import scenes_are_stale


USER_ID = "user-1"
STORY_ID = "story-1"
CHAPTER_ID = "chapter-1"

SCENE_1_START = "Aria stood alone beneath the eastern gate."
SCENE_1_MIDDLE = "Aria crossed the courtyard beneath the red banners."
SCENE_1_END = "The first bell rang over the silent walls."
SCENE_2_START = "Beren entered the council chamber without ceremony."
SCENE_2_END = "The council doors closed behind him at midnight."
SCENE_3_START = "Cora woke before dawn beside the river."
SCENE_3_END = "Sunlight finally broke across the northern hills."


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _long_content() -> str:
    return " ".join(
        [
            SCENE_1_START,
            SCENE_1_MIDDLE,
            *("alpha" for _ in range(340)),
            SCENE_1_END,
            SCENE_2_START,
            *("beta" for _ in range(340)),
            SCENE_2_END,
            SCENE_3_START,
            *("gamma" for _ in range(340)),
            SCENE_3_END,
        ]
    )


def _short_content() -> str:
    return " ".join("short" for _ in range(50))


def _chapter(
    *,
    chapter_id: str = CHAPTER_ID,
    content: str | None = None,
    published: bool = False,
    stale: bool = False,
    updated_at: datetime | None = None,
) -> ChapterRow:
    chapter_content = content if content is not None else _long_content()
    return ChapterRow(
        id=chapter_id,
        story_id=STORY_ID,
        user_id=USER_ID,
        title="Test Chapter",
        content=chapter_content,
        published=published,
        word_count=len(chapter_content.split()),
        next_chapter_id=None,
        prev_chapter_id=None,
        scenes_need_reextraction=stale,
        scenes_extracted_at=None,
        created_at=_now(),
        updated_at=updated_at or _now(),
    )


def _valid_extraction() -> SceneExtraction:
    return SceneExtraction(
        scenes=[
            Scene(
                title="At the eastern gate",
                start_quote=SCENE_1_START,
                end_quote=SCENE_1_END,
                description="Aria crosses the courtyard as the city prepares for the coming council.",
                pov="Aria",
                tension="medium",
                pacing="steady",
                mentioned_entities=["Aria", "Eastern Gate"],
                tags=["setup", "worldbuilding"],
                questions_raised=["Why is Aria waiting at the eastern gate?"],
            ),
            Scene(
                title="The midnight council",
                start_quote=SCENE_2_START,
                end_quote=SCENE_2_END,
                description="Beren enters the council chamber and the meeting continues behind closed doors.",
                pov="Beren",
                tension="high",
                pacing="fast",
                mentioned_entities=["Beren", "Council"],
                tags=["politics", "plot-revelation"],
                questions_raised=["What will the council decide?"],
            ),
            Scene(
                title="Before dawn",
                start_quote=SCENE_3_START,
                end_quote=SCENE_3_END,
                description="Cora wakes beside the river and watches dawn break over the hills.",
                pov="Cora",
                tension="low",
                pacing="slow",
                mentioned_entities=["Cora", "Northern Hills"],
                tags=["reflection", "transition"],
                questions_raised=[],
            ),
        ]
    )


def _scene_row(
    *,
    scene_id: str = "old-scene",
    chapter_id: str = CHAPTER_ID,
    title: str = "Old Scene",
) -> SceneRow:
    now = _now()
    return SceneRow(
        id=scene_id,
        chapter_id=chapter_id,
        story_id=STORY_ID,
        user_id=USER_ID,
        position=0,
        title=title,
        start_quote=SCENE_1_START,
        end_quote=SCENE_1_END,
        description="Previously extracted scene.",
        pov="Aria",
        word_count=100,
        tension="medium",
        pacing="steady",
        mentioned_entities=["Aria"],
        tags=["old"],
        questions_raised=[],
        embedding_model=None,
        embedded_at=None,
        created_at=now,
        updated_at=now,
    )


def _seed_stale_chapters(chapter_repo, count: int) -> list[str]:
    ids: list[str] = []
    for index in range(count):
        chapter_id = f"stale-{index}"
        ids.append(chapter_id)
        chapter_repo.seed(
            _chapter(
                chapter_id=chapter_id,
                published=True,
                stale=True,
                updated_at=_now() - timedelta(minutes=30 - index),
            )
        )
    return ids


@pytest.mark.parametrize("content", [None, _long_content()])
async def test_extract_scenes_raises_not_found_for_missing_chapter(
    content: str | None,
    extraction_context,
):
    service, _, _, _ = extraction_context

    with pytest.raises(NotFoundError):
        await service.extract_scenes(
            chapter_id="missing",
            user_id=USER_ID,
            content=content,
        )


async def test_short_chapter_skips_ai_clears_scenes_and_marks_extracted(
    extraction_context,
):
    service, provider, chapter_repo, scene_repo = extraction_context
    chapter = _chapter(content=_short_content(), stale=True)
    chapter_repo.seed(chapter)
    scene_repo.seed(_scene_row())

    result = await service.extract_scenes(chapter.id, chapter.user_id)

    assert result is None
    assert provider.call_count == 0
    assert await scene_repo.list_by_chapter(chapter.id) == []

    updated = await chapter_repo.get(chapter.id, chapter.user_id)
    assert updated is not None
    assert updated.scenes_extracted_at is not None
    assert updated.scenes_need_reextraction is False


async def test_valid_extraction_replaces_scenes_marks_chapter_and_returns_metadata(
    extraction_context,
):
    service, provider, chapter_repo, scene_repo = extraction_context
    chapter = _chapter(stale=True)
    chapter_repo.seed(chapter)
    scene_repo.seed(_scene_row())
    extraction = _valid_extraction()
    provider.extract_response = extraction

    result = await service.extract_scenes(chapter.id, chapter.user_id)

    assert result is not None
    assert result.scenes_extracted == 3
    assert result.chapter_number == 1
    assert result.story_title == "Test Story"
    assert provider.call_count == 1

    scenes = await scene_repo.list_by_chapter(chapter.id)
    assert [scene.title for scene in scenes] == [
        scene.title for scene in extraction.scenes
    ]
    assert all(scene.id != "old-scene" for scene in scenes)

    updated = await chapter_repo.get(chapter.id, chapter.user_id)
    assert updated is not None
    assert updated.scenes_extracted_at is not None
    assert updated.scenes_need_reextraction is False

    assert scene_repo.last_replace_executor is not None
    assert scene_repo.last_replace_executor is chapter_repo.last_mark_executor


async def test_provider_failure_is_translated_to_internal_error(extraction_context):
    service, provider, chapter_repo, _ = extraction_context
    chapter = _chapter()
    chapter_repo.seed(chapter)
    provider.error = LLMServiceError("provider failed", RuntimeError("boom"))

    with pytest.raises(InternalError, match="LLM service failure"):
        await service.extract_scenes(chapter.id, chapter.user_id)


async def test_replace_failure_rolls_back_existing_extraction(extraction_context):
    service, provider, chapter_repo, scene_repo = extraction_context
    chapter = _chapter(stale=True)
    chapter_repo.seed(chapter)
    scene_repo.seed(_scene_row())
    provider.extract_response = _valid_extraction()
    scene_repo.fail_after_delete = DatabaseError(
        "replace failed",
        RuntimeError("write failed"),
    )

    with pytest.raises(InternalError, match="database error"):
        await service.extract_scenes(chapter.id, chapter.user_id)

    scenes = await scene_repo.list_by_chapter(chapter.id)
    assert [scene.id for scene in scenes] == ["old-scene"]

    updated = await chapter_repo.get(chapter.id, chapter.user_id)
    assert updated is not None
    assert updated.scenes_extracted_at is None
    assert updated.scenes_need_reextraction is True


async def test_mark_extracted_failure_rolls_back_scene_replacement(extraction_context):
    service, provider, chapter_repo, scene_repo = extraction_context
    chapter = _chapter(stale=True)
    chapter_repo.seed(chapter)
    scene_repo.seed(_scene_row())
    provider.extract_response = _valid_extraction()
    chapter_repo.mark_extracted_error = DatabaseError(
        "mark failed",
        RuntimeError("write failed"),
    )

    with pytest.raises(InternalError, match="database error"):
        await service.extract_scenes(chapter.id, chapter.user_id)

    scenes = await scene_repo.list_by_chapter(chapter.id)
    assert [scene.id for scene in scenes] == ["old-scene"]

    updated = await chapter_repo.get(chapter.id, chapter.user_id)
    assert updated is not None
    assert updated.scenes_extracted_at is None
    assert updated.scenes_need_reextraction is True


async def test_invalid_extraction_retries_with_validation_feedback_then_succeeds(
    extraction_context,
    monkeypatch: pytest.MonkeyPatch,
):
    service, provider, _, _ = extraction_context
    valid = _valid_extraction()
    invalid = valid.model_copy(deep=True)
    invalid.scenes[0].pov = "Ghost"
    responses = [invalid, valid]
    prompts: list[str] = []

    async def fake_extract(**kwargs):
        provider.call_count += 1
        prompts.append(kwargs["text"])
        return responses.pop(0)

    monkeypatch.setattr(provider, "extract", fake_extract)

    result = await service._extract_with_feedback(_long_content())

    assert result == valid
    assert provider.call_count == 2
    assert "<previous_extraction_errors>" not in prompts[0]
    assert "<previous_extraction_errors>" in prompts[1]
    assert "pov 'Ghost' not in mentioned_entities" in prompts[1]


async def test_invalid_extraction_stops_after_configured_retry_limit(extraction_context):
    service, provider, _, _ = extraction_context
    invalid = _valid_extraction().model_copy(deep=True)
    invalid.scenes[0].pov = "Ghost"
    provider.extract_response = invalid

    with pytest.raises(InternalError, match="Failed after"):
        await service._extract_with_feedback(_long_content())

    assert provider.call_count == config.ai.max_retries


def test_validation_rejects_empty_extraction(extraction_context):
    service, _, _, _ = extraction_context
    errors = service._validate_extraction(SceneExtraction(scenes=[]), _long_content())
    assert errors == ["extraction must contain at least one scene"]


def test_validation_rejects_too_short_content(extraction_context):
    service, _, _, _ = extraction_context
    errors = service._validate_extraction(_valid_extraction(), _short_content())
    assert errors == ["There is not enough chapter content for a valid extraction."]


@pytest.mark.parametrize(
    ("field", "value", "expected_error"),
    [
        ("start_quote", "", "start_quote can not be empty"),
        ("end_quote", "", "end_quote can not be empty"),
        ("start_quote", "This quote is not in the chapter.", "start_quote not found verbatim"),
        ("end_quote", "This quote is not in the chapter.", "end_quote not found verbatim"),
    ],
)
def test_validation_rejects_invalid_quotes(
    extraction_context,
    field: str,
    value: str,
    expected_error: str,
):
    service, _, _, _ = extraction_context
    extraction = _valid_extraction().model_copy(deep=True)
    setattr(extraction.scenes[0], field, value)

    errors = service._validate_extraction(extraction, _long_content())

    assert any(expected_error in error for error in errors)


def test_validation_rejects_pov_missing_from_entities(extraction_context):
    service, _, _, _ = extraction_context
    extraction = _valid_extraction().model_copy(deep=True)
    extraction.scenes[0].pov = "Ghost"

    errors = service._validate_extraction(extraction, _long_content())

    assert "pov 'Ghost' not in mentioned_entities" in errors


def test_validation_rejects_scene_start_quotes_out_of_order(extraction_context):
    service, _, _, _ = extraction_context
    valid = _valid_extraction()
    extraction = SceneExtraction(
        scenes=[valid.scenes[1], valid.scenes[0], valid.scenes[2]]
    )

    errors = service._validate_extraction(extraction, _long_content())

    assert "scene start_quotes must follow chapter order" in errors


def test_validation_rejects_scene_end_quotes_out_of_order(extraction_context):
    service, _, _, _ = extraction_context
    extraction = _valid_extraction().model_copy(deep=True)
    extraction.scenes[0].end_quote = SCENE_2_END
    extraction.scenes[1].end_quote = SCENE_1_END

    errors = service._validate_extraction(extraction, _long_content())

    assert "scene end_quotes must follow chapter order" in errors


def test_validation_rejects_overlapping_scene_ranges(extraction_context):
    service, _, _, _ = extraction_context
    extraction = _valid_extraction().model_copy(deep=True)
    extraction.scenes[1].start_quote = SCENE_1_MIDDLE

    errors = service._validate_extraction(extraction, _long_content())

    assert any("non-overlapping" in error for error in errors)


def test_validation_rejects_end_boundary_before_start_boundary(extraction_context):
    service, _, _, _ = extraction_context
    extraction = _valid_extraction().model_copy(deep=True)
    extraction.scenes[0].start_quote = SCENE_1_END
    extraction.scenes[0].end_quote = SCENE_1_START

    errors = service._validate_extraction(extraction, _long_content())

    assert "scene 1 end_quote occurs before its start_quote" in errors


def test_matching_scene_anchors_are_not_stale():
    assert scenes_are_stale(_valid_extraction().scenes, _long_content()) is False


@pytest.mark.parametrize("missing_quote", [SCENE_1_START, SCENE_3_END])
def test_missing_scene_anchor_marks_extraction_stale(missing_quote: str):
    content = _long_content().replace(missing_quote, "changed boundary text")
    assert scenes_are_stale(_valid_extraction().scenes, content) is True


def test_blank_scene_anchor_marks_extraction_stale():
    extraction = _valid_extraction().model_copy(deep=True)
    extraction.scenes[0].start_quote = "   "
    assert scenes_are_stale(extraction.scenes, _long_content()) is True


def test_edits_outside_scene_anchors_do_not_mark_extraction_stale():
    content = f"New prefatory note. {_long_content()} New trailing note."
    assert scenes_are_stale(_valid_extraction().scenes, content) is False


async def test_regeneration_queries_four_batches_and_never_exceeds_batch_concurrency(
    extraction_context,
    monkeypatch: pytest.MonkeyPatch,
):
    service, _, chapter_repo, _ = extraction_context
    stale_ids = _seed_stale_chapters(chapter_repo, 12)
    called: list[str] = []
    active = 0
    max_active = 0

    async def fake_extract(chapter_id: str, user_id: str):
        nonlocal active, max_active
        assert user_id == USER_ID
        active += 1
        max_active = max(max_active, active)
        await asyncio.sleep(0)
        called.append(chapter_id)
        active -= 1
        return None

    monkeypatch.setattr(service, "extract_scenes", fake_extract)

    await service.regenerate_stale_batched(batch_size=2)

    assert chapter_repo.last_stale_query == (
        config.jobs.scene_extraction_window_seconds,
        8,
    )
    assert set(called) == set(stale_ids[:8])
    assert max_active == 2


async def test_regeneration_isolates_failures_continues_later_batches_and_counts_successes(
    extraction_context,
    recording_logger,
    monkeypatch: pytest.MonkeyPatch,
):
    service, _, chapter_repo, _ = extraction_context
    stale_ids = _seed_stale_chapters(chapter_repo, 5)
    attempted: list[str] = []

    async def fake_extract(chapter_id: str, user_id: str):
        attempted.append(chapter_id)
        if chapter_id == stale_ids[0]:
            raise RuntimeError("bad chapter")
        return None

    monkeypatch.setattr(service, "extract_scenes", fake_extract)
    monkeypatch.setattr(extraction_module, "logger", recording_logger)

    await service.regenerate_stale_batched(batch_size=2)

    assert attempted == stale_ids
    assert len(recording_logger.warnings) == 1
    assert recording_logger.warnings[0][1]["chapter_id"] == stale_ids[0]
    assert recording_logger.infos == [
        (
            "regenerate_stale_extractions_batched.complete",
            {"extractions_regenerated": 4},
        )
    ]


async def test_regeneration_with_no_stale_chapters_exits_cleanly(
    extraction_context,
    recording_logger,
    monkeypatch: pytest.MonkeyPatch,
):
    service, _, chapter_repo, _ = extraction_context
    called = False

    async def fake_extract(chapter_id: str, user_id: str):
        nonlocal called
        called = True

    monkeypatch.setattr(service, "extract_scenes", fake_extract)
    monkeypatch.setattr(extraction_module, "logger", recording_logger)

    await service.regenerate_stale_batched(batch_size=3)

    assert chapter_repo.last_stale_query == (
        config.jobs.scene_extraction_window_seconds,
        12,
    )
    assert called is False
    assert recording_logger.warnings == []
    assert recording_logger.infos == []
