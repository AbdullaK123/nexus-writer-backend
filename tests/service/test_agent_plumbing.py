import pytest
from src.service.chat.agent import _service_errors_as_text
from src.service.exceptions import NotFoundError
from pydantic_ai import Agent

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


async def test_tool_call(test_agent: Agent):
    result = await test_agent.run("Give me a number")

    assert result.output == "done"