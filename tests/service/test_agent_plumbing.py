import pytest
from src.service.chat.agent import ChatDeps, _service_errors_as_text
from src.service.exceptions import NotFoundError
from pydantic_ai import Agent, ModelMessage, Agent, ModelRequest, ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

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
    chat_deps: ChatDeps
):

    async def model_func(
        messages: list[ModelMessage],
        info: AgentInfo
    ) -> ModelResponse:

        if len(messages) == 1:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        tool_name="list_chapters",
                        args={},
                        tool_call_id="call-1"
                    )
                ]
            )

        latest = messages[-1]

        if isinstance(latest, ModelRequest):
            for part in latest.parts:
                if (
                    isinstance(part, ToolCallPart)
                    and part.content == "This story has no chapters yet."
                ):
                    return ModelResponse(
                        parts=[TextPart("done")]
                    )

        raise AssertionError("Expected empty chapter result")


    fake_model = FunctionModel(function=model_func)

    with test_agent.override(model=fake_model):
        result = await test_agent.run( # type: ignore
            "List my chapters",
            deps=chat_deps # type: ignore
        )

    assert result.output == "done"