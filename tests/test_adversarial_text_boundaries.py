import pytest
from pydantic import TypeAdapter, ValidationError

from src.shared.text_types import (
    CHAT_MESSAGE_MAX,
    CHAPTER_CONTENT_MAX,
    SEARCH_QUERY_MAX,
    TITLE_MAX,
    ChapterContent,
    ChatMessage,
    SearchQuery,
    StoryTitle,
)


@pytest.mark.parametrize(
    ("text_type", "payload"),
    [
        (StoryTitle, "safe\x00evil"),
        (SearchQuery, "safe\x00evil"),
        (ChatMessage, "safe\x00evil"),
        (ChapterContent, "<p>safe\x00evil</p>"),
    ],
)
def test_nul_never_crosses_a_text_boundary(text_type, payload: str) -> None:
    with pytest.raises(ValidationError, match="NUL"):
        TypeAdapter(text_type).validate_python(payload)


@pytest.mark.parametrize("control", ["\u202e", "\u2066", "\u2069", "\u200f"])
def test_single_line_fields_reject_bidi_display_spoofing(control: str) -> None:
    with pytest.raises(ValidationError, match="bidirectional"):
        TypeAdapter(StoryTitle).validate_python(f"invoice{control}gpj.exe")


def test_title_normalization_collapses_invisible_duplicate_spellings() -> None:
    adapter = TypeAdapter(StoryTitle)

    assert adapter.validate_python("  My\u200b   Story  ") == "My Story"
    assert adapter.validate_python("Cafe\u0301") == "Café"


@pytest.mark.parametrize(
    ("text_type", "max_length"),
    [
        (StoryTitle, TITLE_MAX),
        (SearchQuery, SEARCH_QUERY_MAX),
        (ChatMessage, CHAT_MESSAGE_MAX),
        (ChapterContent, CHAPTER_CONTENT_MAX),
    ],
)
def test_giant_padding_is_rejected_before_cleanup(text_type, max_length: int) -> None:
    payload = "x" + (" " * max_length)

    with pytest.raises(ValidationError, match="at most"):
        TypeAdapter(text_type).validate_python(payload)


def test_multiline_chat_normalizes_line_endings_but_preserves_real_lines() -> None:
    value = TypeAdapter(ChatMessage).validate_python("  first\r\nsecond\rthird  ")

    assert value == "first\nsecond\nthird"


def test_chapter_content_does_not_strip_structurally_meaningful_outer_payload() -> None:
    payload = "  <p>Hello</p>  "

    assert TypeAdapter(ChapterContent).validate_python(payload) == payload
