"""Tests for src/service/jobs/extraction.py — regenerate_stale_extractions_batched.

Strategy: mock `extract_scenes` (the AI-calling part) at the job's import site
so we test only the sweep / batch / log logic. Stale `updated_at` values are
set with a follow-up `.update()` to bypass `auto_now=True`.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from loguru import logger

from src.data.models import Extraction, ExtractionType
from src.service.jobs.extraction import regenerate_stale_extractions_batched
from tests.factories import make_chapter, make_story, make_user


async def _make_stale_extraction(
    chapter_id: str,
    *,
    needs_reextraction: bool = True,
    age_seconds: int = 3600,
) -> Extraction:
    """Create an extraction then backdate `updated_at` past the debounce window."""
    extraction = await Extraction.create(
        chapter_id=chapter_id,
        extraction_type=ExtractionType.SCENES,
        needs_reextraction=needs_reextraction,
        data={"scenes": []},
    )
    backdated = datetime.now(timezone.utc) - timedelta(seconds=age_seconds)
    await Extraction.filter(id=extraction.id).update(updated_at=backdated)
    return extraction


async def _seed(n: int, *, needs_reextraction: bool = True, age_seconds: int = 3600):
    user = await make_user()
    story = await make_story(user)
    extractions = []
    for i in range(n):
        chapter = await make_chapter(story, user, title=f"ch{i}")
        extractions.append(
            await _make_stale_extraction(
                chapter.id,
                needs_reextraction=needs_reextraction,
                age_seconds=age_seconds,
            )
        )
    return extractions


@pytest.fixture
def fake_provider():
    return MagicMock(name="AIProvider")


@pytest.fixture
def mock_extract_scenes(mocker):
    """Replace extract_scenes at the job module's import site."""
    return mocker.patch(
        "src.service.jobs.extraction.extract_scenes",
        new=AsyncMock(return_value=None),
    )


class TestRegenerateStaleExtractionsBatched:
    async def test_no_stale_extractions_is_noop(
        self, fake_provider, mock_extract_scenes, mocker
    ):
        spy = mocker.spy(logger, "info")
        await regenerate_stale_extractions_batched(fake_provider)
        mock_extract_scenes.assert_not_awaited()
        assert not any(
            "regenerate_stale_extractions_batched.complete" in str(c.args)
            for c in spy.call_args_list
        )

    async def test_skips_extractions_not_flagged(
        self, fake_provider, mock_extract_scenes
    ):
        await _seed(3, needs_reextraction=False)
        await regenerate_stale_extractions_batched(fake_provider)
        mock_extract_scenes.assert_not_awaited()

    async def test_skips_extractions_inside_debounce_window(
        self, fake_provider, mock_extract_scenes
    ):
        # Fresh rows (default auto_now) are inside the 60s window.
        user = await make_user()
        story = await make_story(user)
        chapter = await make_chapter(story, user)
        await Extraction.create(
            chapter_id=chapter.id,
            extraction_type=ExtractionType.SCENES,
            needs_reextraction=True,
            data={"scenes": []},
        )
        await regenerate_stale_extractions_batched(fake_provider)
        mock_extract_scenes.assert_not_awaited()

    async def test_calls_extract_scenes_once_per_stale_chapter(
        self, fake_provider, mock_extract_scenes
    ):
        extractions = await _seed(3)
        await regenerate_stale_extractions_batched(fake_provider, batch_size=2)
        assert mock_extract_scenes.await_count == 3
        called_ids = {call.args[1] for call in mock_extract_scenes.await_args_list}
        assert called_ids == {e.chapter_id for e in extractions}

    async def test_caps_at_four_times_batch_size(
        self, fake_provider, mock_extract_scenes
    ):
        await _seed(10)
        await regenerate_stale_extractions_batched(fake_provider, batch_size=2)
        # 4 * 2 = 8
        assert mock_extract_scenes.await_count == 8

    async def test_processes_oldest_first(
        self, fake_provider, mock_extract_scenes
    ):
        user = await make_user()
        story = await make_story(user)
        chapters = [await make_chapter(story, user, title=f"c{i}") for i in range(3)]
        ages = [10, 3600, 1800]  # ch0=fresh-ish but past window? 10s -> inside window
        # Use clearly-stale ages so all qualify, but in distinct order.
        ages = [120, 7200, 3600]  # ch0 newest stale, ch1 oldest, ch2 middle
        for ch, age in zip(chapters, ages):
            await _make_stale_extraction(ch.id, age_seconds=age)

        await regenerate_stale_extractions_batched(fake_provider, batch_size=5)

        called_order = [call.args[1] for call in mock_extract_scenes.await_args_list]
        assert called_order == [chapters[1].id, chapters[2].id, chapters[0].id]

    async def test_continues_after_individual_failures(
        self, fake_provider, mocker
    ):
        extractions = await _seed(3)

        async def flaky(_provider, chapter_id):
            if chapter_id == extractions[1].chapter_id:
                raise RuntimeError("boom")

        mocker.patch(
            "src.service.jobs.extraction.extract_scenes",
            new=AsyncMock(side_effect=flaky),
        )
        warn_spy = mocker.spy(logger, "warning")
        info_spy = mocker.spy(logger, "info")

        await regenerate_stale_extractions_batched(fake_provider, batch_size=5)

        assert any("extract_scenes.failed" in str(c.args) for c in warn_spy.call_args_list)
        # 3 attempted, 1 failed => 2 succeeded => completion log fired
        assert any(
            "regenerate_stale_extractions_batched.complete" in str(c.args)
            for c in info_spy.call_args_list
        )

    async def test_logs_completion_only_when_anything_succeeded(
        self, fake_provider, mocker
    ):
        await _seed(2)
        mocker.patch(
            "src.service.jobs.extraction.extract_scenes",
            new=AsyncMock(side_effect=RuntimeError("always fails")),
        )
        info_spy = mocker.spy(logger, "info")

        await regenerate_stale_extractions_batched(fake_provider, batch_size=5)

        assert not any(
            "regenerate_stale_extractions_batched.complete" in str(c.args)
            for c in info_spy.call_args_list
        )
