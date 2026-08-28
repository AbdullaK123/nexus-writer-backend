import pytest
from src.service.chat.agent import _service_errors_as_text
from src.service.exceptions import NotFoundError

async def test_service_errors_as_text():

    @_service_errors_as_text
    async def broken_tool():
        raise NotFoundError("Chapter not found")

    result = await broken_tool()

    assert result == "Tool error: Chapter not found"

async def test_service_errors_as_text_throws_on_infra_failure():

    @_service_errors_as_text
    async def broken_tool():
        raise RuntimeError("BOOM! The database blew up!")

    with pytest.raises(RuntimeError, match="BOOM! The database blew up!"):
        await broken_tool()