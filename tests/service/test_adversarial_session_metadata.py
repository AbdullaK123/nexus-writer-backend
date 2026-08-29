import pytest
from pydantic import ValidationError

from src.data.schemas.auth import ConnectionDetails
from src.shared.text_types import USER_AGENT_MAX


def test_session_user_agent_rejects_nul_before_persistence() -> None:
    with pytest.raises(ValidationError, match="NUL characters are not allowed"):
        ConnectionDetails(
            ip_address="127.0.0.1",
            user_agent="browser\x00poison",
        )


def test_session_user_agent_is_bounded_before_persistence() -> None:
    with pytest.raises(ValidationError, match=f"at most {USER_AGENT_MAX}"):
        ConnectionDetails(
            ip_address="127.0.0.1",
            user_agent="x" * (USER_AGENT_MAX + 1),
        )
