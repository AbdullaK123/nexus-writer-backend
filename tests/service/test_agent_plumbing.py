import pytest
from src.service.chat.agent import ChatDeps, _service_errors_as_text
from src.service.exceptions import NotFoundError
from pydantic_ai import ModelRequest, Agent, ModelMessage, Agent, ModelResponse, RetryPromptPart, TextPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
from tests.service.mocks.chapter import FakeChapterRepository
import pytest_mock

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
    mocker: pytest_mock.MockerFixture
):
    
    spy = mocker.spy(
        chat_deps.chapter_service,
        "get_story_chapters"
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
        result = await test_agent.run( # type: ignore
            "List my chapters",
            deps=chat_deps # type: ignore
        )

    spy.assert_awaited_once_with(
        story_id=chat_deps.story_id,
        user_id=chat_deps.user_id
    )

    assert result.output == "done"


async def test_invalid_tool_call_args(
    test_agent: Agent,
    chat_deps: ChatDeps,
    mocker: pytest_mock.MockerFixture
):
    
    spy = mocker.spy(
        chat_deps.analytics_service,
        "get_prompt_inputs"
    )

    async def model_func(
        messages: list[ModelMessage],
        info: AgentInfo
    ) -> ModelResponse:

        if len(messages) == 1:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        tool_name="run_code",
                        args={
                            "code": "await get_story_analytics(lense='banana')"
                        },
                        tool_call_id="call-1"
                    )
                ]
            )

        return ModelResponse(
            parts=[TextPart('done')]
        )

    fake_model = FunctionModel(function=model_func)

    with test_agent.override(model=fake_model):
        result = await test_agent.run(
            "Give me info about bananas",
            deps=chat_deps # type: ignore
        )

    spy.assert_not_awaited()

async def test_search(
    test_agent: Agent,
    chat_deps: ChatDeps,
    mocker: pytest_mock.MockerFixture
):
    
    spy = mocker.spy(
        chat_deps.story_service,
        "search_story_scenes"
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
            deps=chat_deps, #type: ignore
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
    fake_chapter_repo: FakeChapterRepository
):

    fake_chapter_repo.error = NotFoundError(
        "Chapter lookup exploded"
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

        latest = messages[-1]

        if isinstance(latest, ModelRequest):
            for part in latest.parts:
                if (
                    isinstance(part, ToolReturnPart) and
                    part.content == "Tool error: Chapter lookup exploded"
                ):
                    return ModelResponse(parts=[TextPart("done")])

        raise AssertionError("Expected recoverable chapter tool error")
    
    fake_model = FunctionModel(function=model_func)

    with test_agent.override(model=fake_model):
        result = await test_agent.run( # type: ignore
            "List my chapters",
            deps=chat_deps # type: ignore
        )

    assert result.output == "done"

async def test_tool_call_runtime_error(
    test_agent: Agent,
    chat_deps: ChatDeps,
    fake_chapter_repo: FakeChapterRepository
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
        result = await test_agent.run( # type: ignore
            "List my chapters",
            deps=chat_deps # type: ignore
        )

    assert result.output == 'done'

from src.data.schemas.chapter import ChapterRow


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
                    and part.content.startswith(
                        "Tool error: start_quote not found"
                    )
                ):
                    return ModelResponse(
                        parts=[TextPart("done")]
                    )

        raise AssertionError(
            "Expected missing start_quote tool error"
        )

    fake_model = FunctionModel(function=model_func)

    with test_agent.override(model=fake_model):
        result = await test_agent.run(
            "Read this scene",
            deps=chat_deps, #type: ignore
        )

    assert result.output == "done"