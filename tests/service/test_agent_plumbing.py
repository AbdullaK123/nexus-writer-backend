import pytest
import pytest_mock
from pydantic_ai import (
    Agent,
    ModelMessage,
    ModelRequest,
    ModelResponse,
    RetryPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
)
from pydantic_ai.models.function import AgentInfo, FunctionModel

from src.data.schemas.chapter import ChapterRow
from src.data.schemas.story import StoryRow
from src.infrastructure.ai.prompts import STORY_STATUS_PROMPTS
from src.service.chat.agent import ChatDeps, _service_errors_as_text, build_agent
from src.service.exceptions import NotFoundError
from tests.service.mocks.chapter import FakeChapterRepository


async def test_service_errors_as_text():
    @_service_errors_as_text
    async def broken_tool():
        raise NotFoundError("Chapter not found")

    result = await broken_tool()

    assert result == "Tool error: Chapter not found"


async def test_service_errors_as_text_propagates_unexpected_errors():
    @_service_errors_as_text
    async def broken_tool():
        raise RuntimeError("BOOM! The database blew up!")

    with pytest.raises(RuntimeError, match="BOOM! The database blew up!"):
        await broken_tool()


async def test_tool_call(
    test_agent: Agent,
    chat_deps: ChatDeps,
    mocker: pytest_mock.MockerFixture,
):
    spy = mocker.spy(
        chat_deps.chapter_service,
        "get_story_chapters",
    )

    async def model_func(
        messages: list[ModelMessage],
        info: AgentInfo,
    ) -> ModelResponse:
        if len(messages) == 1:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        tool_name="run_code",
                        args={
                            "code": "await list_chapters()",
                        },
                        tool_call_id="call-1",
                    )
                ]
            )

        return ModelResponse(parts=[TextPart("done")])

    fake_model = FunctionModel(function=model_func)

    with test_agent.override(model=fake_model):
        result = await test_agent.run(  # type: ignore
            "List my chapters",
            deps=chat_deps,  # type: ignore
        )

    spy.assert_awaited_once_with(
        story_id=chat_deps.story_id,
        user_id=chat_deps.user_id,
    )

    assert result.output == "done"


async def test_invalid_tool_call_args(
    test_agent: Agent,
    chat_deps: ChatDeps,
    mocker: pytest_mock.MockerFixture,
):
    spy = mocker.spy(
        chat_deps.analytics_service,
        "get_prompt_inputs",
    )

    async def model_func(
        messages: list[ModelMessage],
        info: AgentInfo,
    ) -> ModelResponse:
        if len(messages) == 1:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        tool_name="run_code",
                        args={
                            "code": "await get_story_analytics(lense='banana')"
                        },
                        tool_call_id="call-1",
                    )
                ]
            )

        return ModelResponse(parts=[TextPart("done")])

    fake_model = FunctionModel(function=model_func)

    with test_agent.override(model=fake_model):
        await test_agent.run(
            "Give me info about bananas",
            deps=chat_deps,  # type: ignore
        )

    spy.assert_not_awaited()


async def test_search(
    test_agent: Agent,
    chat_deps: ChatDeps,
    mocker: pytest_mock.MockerFixture,
):
    spy = mocker.spy(
        chat_deps.story_service,
        "search_story_scenes",
    )

    async def model_func(
        messages: list[ModelMessage],
        info: AgentInfo,
    ) -> ModelResponse:
        if len(messages) == 1:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        tool_name="run_code",
                        args={
                            "code": """await search_scenes_semantic(
    query="betrayal at the harbor",
    tension="high",
    pacing="fast",
    tags=["betrayal", "turning-point"],
    pov="Mara",
    mentioned_entities=["Captain Vale", "Black Fleet"],
    chapter_ids=["chapter-1", "chapter-7"],
    k=13,
)"""
                        },
                        tool_call_id="call-1",
                    )
                ]
            )

        return ModelResponse(parts=[TextPart("done")])

    fake_model = FunctionModel(function=model_func)

    with test_agent.override(model=fake_model):
        await test_agent.run(
            "Search the story",
            deps=chat_deps,  # type: ignore
        )

    spy.assert_awaited_once_with(
        user_id=chat_deps.user_id,
        story_id=chat_deps.story_id,
        query_text="betrayal at the harbor",
        k=13,
        tension="high",
        pacing="fast",
        pov="Mara",
        tags=["betrayal", "turning-point"],
        mentioned_entities=["Captain Vale", "Black Fleet"],
        chapter_ids=["chapter-1", "chapter-7"],
    )


async def test_tool_call_service_error(
    test_agent: Agent,
    chat_deps: ChatDeps,
    fake_chapter_repo: FakeChapterRepository,
):
    fake_chapter_repo.error = NotFoundError("Chapter lookup exploded")

    async def model_func(
        messages: list[ModelMessage],
        info: AgentInfo,
    ) -> ModelResponse:
        if len(messages) == 1:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        tool_name="run_code",
                        args={
                            "code": "await list_chapters()",
                        },
                        tool_call_id="call-1",
                    )
                ]
            )

        latest = messages[-1]

        if isinstance(latest, ModelRequest):
            for part in latest.parts:
                if (
                    isinstance(part, ToolReturnPart)
                    and part.content == "Tool error: Chapter lookup exploded"
                ):
                    return ModelResponse(parts=[TextPart("done")])

        raise AssertionError("Expected recoverable chapter tool error")

    fake_model = FunctionModel(function=model_func)

    with test_agent.override(model=fake_model):
        result = await test_agent.run(  # type: ignore
            "List my chapters",
            deps=chat_deps,  # type: ignore
        )

    assert result.output == "done"


async def test_tool_call_runtime_error(
    test_agent: Agent,
    chat_deps: ChatDeps,
    fake_chapter_repo: FakeChapterRepository,
):
    fake_chapter_repo.error = RuntimeError("database exploded")

    async def model_func(
        messages: list[ModelMessage],
        info: AgentInfo,
    ) -> ModelResponse:
        if len(messages) == 1:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        tool_name="run_code",
                        args={
                            "code": "await list_chapters()",
                        },
                        tool_call_id="call-1",
                    )
                ]
            )

        latest = messages[-1]

        if isinstance(latest, ModelRequest):
            for part in latest.parts:
                if (
                    isinstance(part, RetryPromptPart)
                    and part.tool_name == "run_code"
                    and "RuntimeError: database exploded" in part.content
                ):
                    return ModelResponse(parts=[TextPart("done")])

        raise AssertionError("Expected runtime failure retry prompt")

    fake_model = FunctionModel(function=model_func)

    with test_agent.override(model=fake_model):
        result = await test_agent.run(  # type: ignore
            "List my chapters",
            deps=chat_deps,  # type: ignore
        )

    assert result.output == "done"


async def test_get_scene_text_missing_start_quote_returns_tool_error(
    test_agent: Agent,
    chat_deps: ChatDeps,
    test_chapter: ChapterRow,
):
    async def model_func(
        messages: list[ModelMessage],
        info: AgentInfo,
    ) -> ModelResponse:
        if len(messages) == 1:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        tool_name="run_code",
                        args={
                            "code": f"""await get_scene_text(
    chapter_id={test_chapter.id!r},
    start_quote="THIS QUOTE DOES NOT EXIST",
    end_quote="test content",
)"""
                        },
                        tool_call_id="call-1",
                    )
                ]
            )

        latest = messages[-1]

        if isinstance(latest, ModelRequest):
            for part in latest.parts:
                if (
                    isinstance(part, ToolReturnPart)
                    and isinstance(part.content, str)
                    and part.content.startswith("Tool error: start_quote not found")
                ):
                    return ModelResponse(parts=[TextPart("done")])

        raise AssertionError("Expected missing start_quote tool error")

    fake_model = FunctionModel(function=model_func)

    with test_agent.override(model=fake_model):
        result = await test_agent.run(
            "Read this scene",
            deps=chat_deps,  # type: ignore
        )

    assert result.output == "done"


async def test_get_scene_text_missing_end_quote_returns_tool_error(
    test_agent: Agent,
    chat_deps: ChatDeps,
    test_chapter: ChapterRow,
):
    async def model_func(
        messages: list[ModelMessage],
        info: AgentInfo,
    ) -> ModelResponse:
        if len(messages) == 1:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        tool_name="run_code",
                        args={
                            "code": f"""await get_scene_text(
    chapter_id={test_chapter.id!r},
    start_quote="test",
    end_quote="THIS QUOTE DOES NOT EXIST",
)"""
                        },
                        tool_call_id="call-1",
                    )
                ]
            )

        latest = messages[-1]

        if isinstance(latest, ModelRequest):
            for part in latest.parts:
                if (
                    isinstance(part, ToolReturnPart)
                    and isinstance(part.content, str)
                    and part.content.startswith(
                        "Tool error: end_quote not found after start_quote"
                    )
                ):
                    return ModelResponse(parts=[TextPart("done")])

        raise AssertionError("Expected missing end_quote tool error")

    fake_model = FunctionModel(function=model_func)

    with test_agent.override(model=fake_model):
        result = await test_agent.run(
            "Read this scene",
            deps=chat_deps,  # type: ignore
        )

    assert result.output == "done"


async def test_get_scene_text_reversed_quotes_fail_safely(
    test_agent: Agent,
    chat_deps: ChatDeps,
    fake_chapter_repo: FakeChapterRepository,
):
    chapter = await fake_chapter_repo.create(
        story_id=chat_deps.story_id,
        user_id=chat_deps.user_id,
        title="Reversed anchors",
        content="END MARKER\nscene prose\nSTART MARKER",
        word_count=5,
    )

    async def model_func(
        messages: list[ModelMessage],
        info: AgentInfo,
    ) -> ModelResponse:
        if len(messages) == 1:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        tool_name="run_code",
                        args={
                            "code": f"""await get_scene_text(
    chapter_id={chapter.id!r},
    start_quote="START MARKER",
    end_quote="END MARKER",
)"""
                        },
                        tool_call_id="call-1",
                    )
                ]
            )

        latest = messages[-1]

        if isinstance(latest, ModelRequest):
            for part in latest.parts:
                if (
                    isinstance(part, ToolReturnPart)
                    and isinstance(part.content, str)
                    and part.content.startswith(
                        "Tool error: end_quote not found after start_quote"
                    )
                ):
                    return ModelResponse(parts=[TextPart("done")])

        raise AssertionError("Expected reversed quote tool error")

    fake_model = FunctionModel(function=model_func)

    with test_agent.override(model=fake_model):
        result = await test_agent.run(
            "Read this scene",
            deps=chat_deps,  # type: ignore
        )

    assert result.output == "done"


async def test_get_chapter_strips_html_before_returning_prose(
    test_agent: Agent,
    chat_deps: ChatDeps,
    fake_chapter_repo: FakeChapterRepository,
):
    chapter = await fake_chapter_repo.create(
        story_id=chat_deps.story_id,
        user_id=chat_deps.user_id,
        title="HTML chapter",
        content="<p>Hello <strong>world</strong>.</p><p>Second line.</p>",
        word_count=4,
    )

    async def model_func(
        messages: list[ModelMessage],
        info: AgentInfo,
    ) -> ModelResponse:
        if len(messages) == 1:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        tool_name="run_code",
                        args={
                            "code": f"await get_chapter(chapter_id={chapter.id!r})"
                        },
                        tool_call_id="call-1",
                    )
                ]
            )

        latest = messages[-1]

        if isinstance(latest, ModelRequest):
            for part in latest.parts:
                if isinstance(part, ToolReturnPart) and isinstance(part.content, str):
                    assert "Hello world." in part.content
                    assert "Second line." in part.content
                    assert "<p>" not in part.content
                    assert "<strong>" not in part.content
                    return ModelResponse(parts=[TextPart("done")])

        raise AssertionError("Expected plain-text chapter tool result")

    fake_model = FunctionModel(function=model_func)

    with test_agent.override(model=fake_model):
        result = await test_agent.run(
            "Read the chapter",
            deps=chat_deps,  # type: ignore
        )

    assert result.output == "done"


async def test_empty_scene_search_does_not_fetch_chapter_metadata(
    test_agent: Agent,
    chat_deps: ChatDeps,
    mocker: pytest_mock.MockerFixture,
):
    chapter_spy = mocker.spy(
        chat_deps.chapter_service,
        "get_story_chapters",
    )

    async def model_func(
        messages: list[ModelMessage],
        info: AgentInfo,
    ) -> ModelResponse:
        if len(messages) == 1:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        tool_name="run_code",
                        args={
                            "code": "await search_scenes_semantic(query='nothing matches this')"
                        },
                        tool_call_id="call-1",
                    )
                ]
            )

        latest = messages[-1]

        if isinstance(latest, ModelRequest):
            for part in latest.parts:
                if (
                    isinstance(part, ToolReturnPart)
                    and part.content == "No matching scenes."
                ):
                    return ModelResponse(parts=[TextPart("done")])

        raise AssertionError("Expected empty scene-search result")

    fake_model = FunctionModel(function=model_func)

    with test_agent.override(model=fake_model):
        result = await test_agent.run(
            "Search for something absent",
            deps=chat_deps,  # type: ignore
        )

    chapter_spy.assert_not_awaited()
    assert result.output == "done"


async def test_story_lifecycle_instruction_comes_from_chat_deps(
    test_agent: Agent,
    chat_deps: ChatDeps,
):
    async def model_func(
        messages: list[ModelMessage],
        info: AgentInfo,
    ) -> ModelResponse:
        latest = messages[-1]
        assert isinstance(latest, ModelRequest)
        assert latest.instructions == STORY_STATUS_PROMPTS[chat_deps.story_status]
        return ModelResponse(parts=[TextPart("done")])

    fake_model = FunctionModel(function=model_func)

    with test_agent.override(model=fake_model):
        result = await test_agent.run(
            "Inspect lifecycle wiring",
            deps=chat_deps,  # type: ignore
        )

    assert result.output == "done"


async def test_custom_system_prompt_does_not_get_story_lifecycle_instruction(
    chat_deps: ChatDeps,
):
    agent = build_agent(
        "openai/gpt-5.4",
        system_prompt="CUSTOM TEST PROMPT",
    )

    async def model_func(
        messages: list[ModelMessage],
        info: AgentInfo,
    ) -> ModelResponse:
        latest = messages[-1]
        assert isinstance(latest, ModelRequest)
        assert latest.instructions is None
        return ModelResponse(parts=[TextPart("done")])

    fake_model = FunctionModel(function=model_func)

    with agent.override(model=fake_model):
        result = await agent.run(
            "Inspect custom prompt wiring",
            deps=chat_deps,
        )

    assert result.output == "done"


@pytest.mark.xfail(
    strict=True,
    reason=(
        "get_chapter/get_scene_text currently scope chapter lookup by user_id only; "
        "same-user chapters from another story are readable through the agent"
    ),
)
async def test_get_chapter_cannot_escape_current_story(
    test_agent: Agent,
    chat_deps: ChatDeps,
    other_story: StoryRow,
    fake_chapter_repo: FakeChapterRepository,
):
    foreign_chapter = await fake_chapter_repo.create(
        story_id=other_story.id,
        user_id=chat_deps.user_id,
        title="Other story secret",
        content="SECRET FROM ANOTHER STORY",
        word_count=4,
    )

    async def model_func(
        messages: list[ModelMessage],
        info: AgentInfo,
    ) -> ModelResponse:
        if len(messages) == 1:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        tool_name="run_code",
                        args={
                            "code": f"await get_chapter(chapter_id={foreign_chapter.id!r})"
                        },
                        tool_call_id="call-1",
                    )
                ]
            )

        latest = messages[-1]

        if isinstance(latest, ModelRequest):
            for part in latest.parts:
                if (
                    isinstance(part, ToolReturnPart)
                    and isinstance(part.content, str)
                    and part.content.startswith("Tool error:")
                ):
                    return ModelResponse(parts=[TextPart("done")])

        raise AssertionError("Expected cross-story chapter access to be rejected")

    fake_model = FunctionModel(function=model_func)

    with test_agent.override(model=fake_model):
        result = await test_agent.run(
            "Read that chapter",
            deps=chat_deps,  # type: ignore
        )

    assert result.output == "done"
