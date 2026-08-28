from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import cast

from pydantic_ai import ModelRequest, ToolCallPart, ToolReturnPart

from src.data.schemas.chapter import (
    ChapterContentResponse,
    ChapterListItem,
    ChapterListResponse,
)
from src.data.schemas.enums import StoryStatus
from src.data.schemas.scene import SceneSearchResponse, VocabularyItem, VocabularyListResponse
from src.service.analytics.service import AnalyticsService
from src.service.chapter.service import ChapterService
from src.service.chat.agent import ChatDeps, build_agent
from src.service.exceptions import InternalError, NotFoundError
from src.service.story.service import StoryService

from .dataset import EvalChapter, StoryAgentEvalInput


USER_ID = "eval-user"
STORY_ID = "eval-story"
STORY_TITLE = "Eval Story"
_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


@dataclass(frozen=True)
class StoryAgentRun:
    answer: str
    called_tools: tuple[str, ...]


class EvalChapterService:
    def __init__(self, inputs: StoryAgentEvalInput):
        self._inputs = inputs

    async def get_chapter_with_navigation(
        self,
        chapter_id: str,
        user_id: str,
        as_html: bool = True,
    ) -> ChapterContentResponse:
        if user_id != USER_ID:
            raise NotFoundError("Chapter not found")

        chapter_number = _chapter_number(chapter_id)
        chapter = _get_chapter(self._inputs, chapter_number)
        previous_id = f"chapter-{chapter_number - 1}" if chapter_number > 1 else None
        next_id = (
            f"chapter-{chapter_number + 1}"
            if chapter_number < len(self._inputs.chapters)
            else None
        )
        return ChapterContentResponse(
            id=chapter_id,
            chapter_number=chapter_number,
            title=chapter.title,
            published=True,
            content=chapter.content,
            story_id=STORY_ID,
            story_title=STORY_TITLE,
            word_count=len(chapter.content.split()),
            created_at=_NOW,
            updated_at=_NOW,
            previous_chapter_id=previous_id,
            next_chapter_id=next_id,
        )

    async def get_story_chapters(
        self,
        story_id: str,
        user_id: str,
    ) -> ChapterListResponse:
        if story_id != STORY_ID or user_id != USER_ID:
            raise NotFoundError("Story not found")

        items = [
            ChapterListItem(
                story_id=STORY_ID,
                chapter_id=f"chapter-{index}",
                chapter_number=index,
                word_count=len(chapter.content.split()),
                story_title=STORY_TITLE,
                chapter_title=chapter.title,
                published=True,
                updated_at=_NOW,
            )
            for index, chapter in enumerate(self._inputs.chapters, start=1)
        ]
        return ChapterListResponse(
            story_id=STORY_ID,
            story_title=STORY_TITLE,
            story_status=StoryStatus(self._inputs.story_status),
            story_last_updated=_NOW,
            chapters=items,
        )


class EvalStoryService:
    def __init__(self, inputs: StoryAgentEvalInput):
        self._inputs = inputs

    async def search_story_scenes(
        self,
        *,
        user_id: str,
        story_id: str,
        query_text: str,
        k: int,
        tension: str | None = None,
        pacing: str | None = None,
        pov: str | None = None,
        tags: list[str] | None = None,
        mentioned_entities: list[str] | None = None,
        chapter_ids: list[str] | None = None,
    ) -> list[SceneSearchResponse]:
        self._raise_if_failed("search_scenes_semantic")
        if user_id != USER_ID or story_id != STORY_ID:
            return []

        results: list[SceneSearchResponse] = []
        for chapter_index, chapter in enumerate(self._inputs.chapters, start=1):
            chapter_id = f"chapter-{chapter_index}"
            if chapter_ids and chapter_id not in chapter_ids:
                continue

            for scene_index, scene in enumerate(chapter.scenes, start=1):
                if tension is not None and scene.tension != tension:
                    continue
                if pacing is not None and scene.pacing != pacing:
                    continue
                if pov is not None and scene.pov != pov:
                    continue
                if tags and not set(tags).intersection(scene.tags):
                    continue
                if mentioned_entities and not set(mentioned_entities).intersection(
                    scene.mentioned_entities
                ):
                    continue

                results.append(
                    SceneSearchResponse(
                        id=f"scene-{chapter_index}-{scene_index}",
                        chapter_id=chapter_id,
                        chapter_number=chapter_index,
                        chapter_title=chapter.title,
                        story_id=STORY_ID,
                        title=scene.title,
                        description=scene.description,
                        start_quote=scene.start_quote,
                        end_quote=scene.end_quote,
                        tension=scene.tension,
                        pacing=scene.pacing,
                        mentioned_entities=list(scene.mentioned_entities),
                        tags=list(scene.tags),
                        questions_raised=list(scene.questions_raised),
                        score=1.0,
                        created_at=_NOW,
                        updated_at=_NOW,
                    )
                )

        return results[:k]

    async def list_story_tags(
        self,
        *,
        user_id: str,
        story_id: str,
    ) -> VocabularyListResponse:
        self._raise_if_failed("list_story_tags")
        return _vocabulary(self._inputs, "tags")

    async def list_story_entities(
        self,
        *,
        user_id: str,
        story_id: str,
    ) -> VocabularyListResponse:
        self._raise_if_failed("list_story_entities")
        return _vocabulary(self._inputs, "entities")

    async def list_povs(
        self,
        *,
        user_id: str,
        story_id: str,
    ) -> VocabularyListResponse:
        self._raise_if_failed("list_povs")
        counts = Counter(
            scene.pov
            for chapter in self._inputs.chapters
            for scene in chapter.scenes
        )
        return VocabularyListResponse(
            items=[
                VocabularyItem(value=value, count=count)
                for value, count in counts.most_common()
            ]
        )

    def _raise_if_failed(self, tool_name: str) -> None:
        for failure in self._inputs.tool_failures:
            if failure.tool_name == tool_name:
                raise InternalError(failure.message)


class EvalAnalyticsService:
    def __init__(self, inputs: StoryAgentEvalInput):
        self._inputs = inputs

    async def get_prompt_inputs(
        self,
        *,
        story_id: str,
        user_id: str,
        lense: str,
    ) -> dict[str, str]:
        for failure in self._inputs.tool_failures:
            if failure.tool_name == "get_story_analytics":
                raise InternalError(failure.message)

        for analytics in self._inputs.analytics:
            if analytics.lense == lense:
                return dict(analytics.tables)
        return {}


def make_deps(inputs: StoryAgentEvalInput) -> ChatDeps:
    return ChatDeps(
        user_id=USER_ID,
        story_id=STORY_ID,
        story_status=StoryStatus(inputs.story_status),
        chapter_service=cast(ChapterService, EvalChapterService(inputs)),
        analytics_service=cast(AnalyticsService, EvalAnalyticsService(inputs)),
        story_service=cast(StoryService, EvalStoryService(inputs)),
    )


def make_task(model_name: str):
    agent = build_agent(model_name)

    async def run_story_agent(inputs: StoryAgentEvalInput) -> StoryAgentRun:
        result = await agent.run(inputs.user_message, deps=make_deps(inputs))
        return StoryAgentRun(
            answer=result.output,
            called_tools=_extract_called_tools(result.all_messages()), # type: ignore
        )

    return run_story_agent


def _extract_called_tools(messages: list[object]) -> tuple[str, ...]:
    called: list[str] = []
    for message in messages:
        if not isinstance(message, ModelRequest):
            continue
        for part in message.parts:
            if not isinstance(part, ToolReturnPart):
                continue
            metadata = part.metadata or {}
            nested_calls = metadata.get("tool_calls")
            if not isinstance(nested_calls, dict):
                continue
            for nested_call in nested_calls.values():
                if isinstance(nested_call, ToolCallPart):
                    called.append(nested_call.tool_name)
    return tuple(dict.fromkeys(called))


def _chapter_number(chapter_id: str) -> int:
    prefix = "chapter-"
    if not chapter_id.startswith(prefix):
        raise NotFoundError("Chapter not found")
    try:
        return int(chapter_id.removeprefix(prefix))
    except ValueError as exc:
        raise NotFoundError("Chapter not found") from exc


def _get_chapter(inputs: StoryAgentEvalInput, chapter_number: int) -> EvalChapter:
    index = chapter_number - 1
    if index < 0 or index >= len(inputs.chapters):
        raise NotFoundError("Chapter not found")
    return inputs.chapters[index]


def _vocabulary(
    inputs: StoryAgentEvalInput,
    field: str,
) -> VocabularyListResponse:
    values: list[str] = []
    for chapter in inputs.chapters:
        for scene in chapter.scenes:
            if field == "tags":
                values.extend(scene.tags)
            else:
                values.extend(scene.mentioned_entities)
    counts = Counter(values)
    return VocabularyListResponse(
        items=[
            VocabularyItem(value=value, count=count)
            for value, count in counts.most_common()
        ]
    )
