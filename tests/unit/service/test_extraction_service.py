"""Tests for ExtractionService — extract_scenes + regenerate_stale_batched.

Strategy: mock ChapterRepository, SceneRepository and the AI provider. Stub
`scene_repo.pool.acquire()` and `conn.transaction()` to be async-context-
managers so the transactional path is exercised without touching a DB.
"""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from loguru import logger

from src.data.schemas import ChapterRow, Scene, SceneExtraction
from src.service.exceptions import NotFoundError
from src.service.extraction import ExtractionService
from src.service.extraction.service import _extract_and_validate  # noqa: F401


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _chapter(
    *, id: str = "ch1", story_id: str = "s1", user_id: str = "u1",
    content: str = "<p>Once upon a time, there was a thing.</p>",
) -> ChapterRow:
    return ChapterRow(
        id=id, story_id=story_id, user_id=user_id, title="t",
        content=content, published=False, word_count=10,
        next_chapter_id=None, prev_chapter_id=None,
        created_at=_now(), updated_at=_now(),
    )


def _make_pool_mock():
    conn = MagicMock(name="conn")

    @asynccontextmanager
    async def _txn():
        yield None
    conn.transaction = MagicMock(side_effect=_txn)

    @asynccontextmanager
    async def _acquire():
        yield conn
    pool = MagicMock(name="pool")
    pool.acquire = MagicMock(side_effect=_acquire)
    return pool


def _chapter_repo_mock():
    repo = MagicMock(name="ChapterRepository")
    repo.get_for_system = AsyncMock(return_value=None)
    repo.pool = _make_pool_mock()
    return repo


def _scene_repo_mock():
    repo = MagicMock(name="SceneRepository")
    repo.list_stale_chapter_ids = AsyncMock(return_value=[])
    repo.replace_for_chapter = AsyncMock(return_value=None)
    repo.mark_chapter_extracted = AsyncMock(return_value=None)
    repo.pool = _make_pool_mock()
    return repo


def _provider_mock():
    return MagicMock(name="AIProvider")


def _service(provider=None, chapter_repo=None, scene_repo=None) -> ExtractionService:
    return ExtractionService(
        provider or _provider_mock(),
        chapter_repo or _chapter_repo_mock(),
        scene_repo or _scene_repo_mock(),
    )


# ─── extract_scenes ──────────────────────────────────────────────────────────


class TestExtractScenes:
    async def test_raises_not_found_when_chapter_missing(self):
        svc = _service()
        with pytest.raises(NotFoundError):
            await svc.extract_scenes("missing")

    async def test_replaces_scenes_and_marks_extracted(self, mocker):
        ch = _chapter(content="<p>Once upon a time.</p>")
        chapter_repo = _chapter_repo_mock()
        chapter_repo.get_for_system = AsyncMock(return_value=ch)
        scene_repo = _scene_repo_mock()
        svc = _service(chapter_repo=chapter_repo, scene_repo=scene_repo)

        scenes = [Scene(
            title="t",
            start_quote="Once",
            end_quote="time.",
            description="d",
            tension="low",
            pacing="slow",
            mentioned_entities=[],
            tags=[],
            questions_raised=[],
        )]
        mocker.patch(
            "src.service.extraction.service._extract_and_validate",
            new=AsyncMock(return_value=SceneExtraction(scenes=scenes)),
        )

        await svc.extract_scenes("ch1")

        scene_repo.replace_for_chapter.assert_awaited_once()
        kwargs = scene_repo.replace_for_chapter.await_args.kwargs
        assert kwargs["chapter_id"] == "ch1"
        assert kwargs["story_id"] == "s1"
        assert kwargs["user_id"] == "u1"
        assert kwargs["scenes"] == scenes
        scene_repo.mark_chapter_extracted.assert_awaited_once()


# ─── regenerate_stale_batched ────────────────────────────────────────────────


def _set_stale(scene_repo, chapter_ids: list[str]) -> None:
    async def _impl(*, window_seconds, limit):
        return chapter_ids[:limit]
    scene_repo.list_stale_chapter_ids = AsyncMock(side_effect=_impl)


class TestRegenerateStaleBatched:
    async def test_no_stale_chapters_is_noop(self, mocker):
        scene_repo = _scene_repo_mock()
        svc = _service(scene_repo=scene_repo)
        spy_extract = mocker.patch.object(svc, "extract_scenes", new=AsyncMock())
        spy_log = mocker.spy(logger, "info")

        await svc.regenerate_stale_batched()

        spy_extract.assert_not_awaited()
        assert not any(
            "regenerate_stale_extractions_batched.complete" in str(c.args)
            for c in spy_log.call_args_list
        )

    async def test_calls_extract_once_per_stale_chapter(self, mocker):
        scene_repo = _scene_repo_mock()
        _set_stale(scene_repo, [f"ch-{i}" for i in range(3)])
        svc = _service(scene_repo=scene_repo)
        spy = mocker.patch.object(svc, "extract_scenes", new=AsyncMock())

        await svc.regenerate_stale_batched(batch_size=2)

        assert spy.await_count == 3
        ids = {c.args[0] for c in spy.await_args_list}
        assert ids == {"ch-0", "ch-1", "ch-2"}

    async def test_caps_at_four_times_batch_size(self, mocker):
        scene_repo = _scene_repo_mock()
        _set_stale(scene_repo, [f"ch-{i}" for i in range(20)])
        svc = _service(scene_repo=scene_repo)
        spy = mocker.patch.object(svc, "extract_scenes", new=AsyncMock())

        await svc.regenerate_stale_batched(batch_size=2)

        assert spy.await_count == 8

    async def test_processes_in_repo_order(self, mocker):
        scene_repo = _scene_repo_mock()
        ordered = ["ch-oldest", "ch-middle", "ch-newest"]
        _set_stale(scene_repo, ordered)
        svc = _service(scene_repo=scene_repo)
        spy = mocker.patch.object(svc, "extract_scenes", new=AsyncMock())

        await svc.regenerate_stale_batched(batch_size=5)

        called_order = [c.args[0] for c in spy.await_args_list]
        assert called_order == ordered

    async def test_continues_after_individual_failures(self, mocker):
        scene_repo = _scene_repo_mock()
        _set_stale(scene_repo, ["ch-0", "ch-1", "ch-2"])
        svc = _service(scene_repo=scene_repo)

        async def flaky(chapter_id):
            if chapter_id == "ch-1":
                raise RuntimeError("boom")

        mocker.patch.object(svc, "extract_scenes", new=AsyncMock(side_effect=flaky))
        warn_spy = mocker.spy(logger, "warning")
        info_spy = mocker.spy(logger, "info")

        await svc.regenerate_stale_batched(batch_size=5)

        assert any(
            "extract_scenes.failed" in str(c.args) for c in warn_spy.call_args_list
        )
        assert any(
            "regenerate_stale_extractions_batched.complete" in str(c.args)
            for c in info_spy.call_args_list
        )

    async def test_logs_completion_only_when_anything_succeeded(self, mocker):
        scene_repo = _scene_repo_mock()
        _set_stale(scene_repo, ["ch-0", "ch-1"])
        svc = _service(scene_repo=scene_repo)
        mocker.patch.object(
            svc, "extract_scenes",
            new=AsyncMock(side_effect=RuntimeError("nope")),
        )
        info_spy = mocker.spy(logger, "info")

        await svc.regenerate_stale_batched(batch_size=5)

        assert not any(
            "regenerate_stale_extractions_batched.complete" in str(c.args)
            for c in info_spy.call_args_list
        )
