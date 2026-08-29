import pytest
from pydantic import TypeAdapter, ValidationError

from src.shared.text_types import (
    CHAT_MESSAGE_MAX,
    CHAPTER_CONTENT_MAX,
    SEARCH_QUERY_MAX,
    TITLE_MAX,
    ChatMessage,
    ChapterContent,
    SearchQuery,
    StoryTitle,
)


def adapter(tp):
    return TypeAdapter(tp)


@pytest.mark.parametrize(
    "tp,value",
    [
        (StoryTitle, "safe\x00evil"),
        (SearchQuery, "search\x00payload"),
        (ChatMessage, "hello\x00world"),
        (ChapterContent, "<p>hello</p>\x00"),
    ],
)
def test_nul_is_rejected_at_schema_boundary(tp, value):
    with pytest.raises(ValidationError, match="NUL characters are not allowed"):
        adapter(tp).validate_python(value)


@pytest.mark.parametrize(
    "tp,value",
    [
        (StoryTitle, "invoice\u202Egpj.exe"),
        (SearchQuery, "character\u2066secret\u2069"),
    ],
)
def test_bidi_formatting_controls_are_rejected_in_single_line_inputs(tp, value):
    with pytest.raises(ValidationError, match="bidirectional formatting controls"):
        adapter(tp).validate_python(value)


def test_story_title_collapses_invisible_and_whitespace_confusables():
    value = "  My\u200b\t\n   Story  "
    assert adapter(StoryTitle).validate_python(value) == "My Story"


def test_single_line_raw_length_is_bounded_before_cleanup_can_shrink_it():
    # Attackers must not be able to send megabytes of disposable whitespace or
    # controls and rely on normalization to shrink it under the business limit.
    oversized = "A" + (" " * TITLE_MAX)
    with pytest.raises(ValidationError, match=f"at most {TITLE_MAX}"):
        adapter(StoryTitle).validate_python(oversized)


def test_search_query_rejects_oversized_padding_before_embedding():
    oversized = "needle" + (" " * SEARCH_QUERY_MAX)
    with pytest.raises(ValidationError, match=f"at most {SEARCH_QUERY_MAX}"):
        adapter(SearchQuery).validate_python(oversized)


def test_chat_message_rejects_oversized_payload_before_ai_work():
    with pytest.raises(ValidationError, match=f"at most {CHAT_MESSAGE_MAX}"):
        adapter(ChatMessage).validate_python("x" * (CHAT_MESSAGE_MAX + 1))


def test_chapter_content_rejects_oversized_payload_before_html_processing():
    with pytest.raises(ValidationError, match=f"at most {CHAPTER_CONTENT_MAX}"):
        adapter(ChapterContent).validate_python("x" * (CHAPTER_CONTENT_MAX + 1))


def test_multiline_chat_normalizes_line_endings_and_strips_unsafe_controls():
    value = "  first\r\nsecond\x01\rthird  "
    assert adapter(ChatMessage).validate_python(value) == "first\nsecond\nthird"


def test_multiline_prose_preserves_join_controls_used_by_real_languages():
    value = "می\u200cروم"
    assert adapter(ChatMessage).validate_python(value) == value
