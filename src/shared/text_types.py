from __future__ import annotations

import re
import unicodedata
from functools import partial
from typing import Annotated, Final, TypeAlias
from src.infrastructure.config.settings import config as app_config
from pydantic import BeforeValidator, Field

__all__ = [
    "Username",
    "PasswordInput",
    "AuthTokenInput",
    "StoryTitle",
    "ChapterTitle",
    "ThreadTitle",
    "SceneTitle",
    "SearchQuery",
    "ChatMessage",
    "ChapterContent",
    "StoryContext",
    "SceneQuote",
    "SceneDescription",
    "EntityName",
    "SceneTag",
    "NarrativeQuestion",
    "NotificationMessage",
    "UserAgent",
]

USERNAME_MAX: Final = 100
PASSWORD_MAX: Final = 128
AUTH_TOKEN_MAX: Final = 256
TITLE_MAX: Final = 255
SEARCH_QUERY_MAX: Final = 500
CHAT_MESSAGE_MAX: Final = 20_000
CHAPTER_CONTENT_MAX: Final = 250_000
STORY_CONTEXT_MAX: Final = 100_000
SCENE_QUOTE_MAX: Final = 2_000
SCENE_DESCRIPTION_MAX: Final = 4_000
ENTITY_NAME_MAX: Final = 255
TAG_MAX: Final = 64
QUESTION_MAX: Final = 1_000
NOTIFICATION_MESSAGE_MAX: Final = 1_000
USER_AGENT_MAX: Final = 512

_STRIPPED_CONTROL_CODEPOINTS: Final[frozenset[int]] = frozenset(
    {cp for cp in range(0x00, 0x20) if cp not in (0x09, 0x0A, 0x0D)}
    | set(range(0x7F, 0xA0))
)

_INVISIBLE_FORMATTING_CODEPOINTS: Final[frozenset[int]] = frozenset(
    {0x00AD, 0x034F, 0x180E, 0x200B, 0x2060, 0xFEFF}
)

_JOIN_CONTROL_CODEPOINTS: Final[frozenset[int]] = frozenset({0x200C, 0x200D})

_BIDI_CONTROL_CODEPOINTS: Final[frozenset[int]] = frozenset(
    {
        0x061C, 0x200E, 0x200F, 0x202A, 0x202B, 0x202C, 0x202D, 0x202E,
        0x2066, 0x2067, 0x2068, 0x2069,
    }
)

_SINGLE_LINE_TRANSLATION: Final = str.maketrans(
    {
        **{cp: None for cp in _STRIPPED_CONTROL_CODEPOINTS},
        **{cp: None for cp in _INVISIBLE_FORMATTING_CODEPOINTS},
        **{cp: None for cp in _JOIN_CONTROL_CODEPOINTS},
        0x09: " ", 0x0A: " ", 0x0D: " ", 0x2028: " ", 0x2029: " ",
    }
)

_MULTILINE_TRANSLATION: Final = str.maketrans(
    {
        **{cp: None for cp in _STRIPPED_CONTROL_CODEPOINTS},
        **{cp: None for cp in _INVISIBLE_FORMATTING_CODEPOINTS},
        0x2028: "\n", 0x2029: "\n",
    }
)

_WHITESPACE_RUN = re.compile(r"\s+")


def _require_string(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("value must be a string")
    return value


def _guard_raw_length(value: str, max_length: int) -> None:
    if len(value) > max_length:
        raise ValueError(f"value must contain at most {max_length} characters")


def _reject_nul(value: str) -> None:
    if "\x00" in value:
        raise ValueError("NUL characters are not allowed")


def _reject_bidi_controls(value: str) -> None:
    if any(ord(ch) in _BIDI_CONTROL_CODEPOINTS for ch in value):
        raise ValueError("bidirectional formatting controls are not allowed")


def _prepare_single_line(
    value: object,
    *,
    max_length: int,
    collapse_whitespace: bool = True,
) -> str:
    text = _require_string(value)
    _guard_raw_length(text, max_length)
    _reject_nul(text)
    _reject_bidi_controls(text)
    text = unicodedata.normalize("NFC", text)
    text = text.translate(_SINGLE_LINE_TRANSLATION)
    text = text.strip()
    if collapse_whitespace:
        text = _WHITESPACE_RUN.sub(" ", text)
    return text


def _prepare_multiline(
    value: object,
    *,
    max_length: int,
    strip_outer_whitespace: bool,
    reject_bidi_controls: bool = False,
) -> str:
    text = _require_string(value)
    _guard_raw_length(text, max_length)
    _reject_nul(text)
    if reject_bidi_controls:
        _reject_bidi_controls(text)
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.translate(_MULTILINE_TRANSLATION)
    if strip_outer_whitespace:
        text = text.strip()
    return text


def _prepare_opaque(value: object, *, max_length: int) -> str:
    """Bound an opaque string without changing its meaningful contents."""
    text = _require_string(value)
    _guard_raw_length(text, max_length)
    _reject_nul(text)
    return text


def _single_line(max_length: int, *, collapse_whitespace: bool = True) -> BeforeValidator:
    return BeforeValidator(
        partial(
            _prepare_single_line,
            max_length=max_length,
            collapse_whitespace=collapse_whitespace,
        )
    )


def _multiline(
    max_length: int,
    *,
    strip_outer_whitespace: bool,
    reject_bidi_controls: bool = False,
) -> BeforeValidator:
    return BeforeValidator(
        partial(
            _prepare_multiline,
            max_length=max_length,
            strip_outer_whitespace=strip_outer_whitespace,
            reject_bidi_controls=reject_bidi_controls,
        )
    )


def _opaque(max_length: int) -> BeforeValidator:
    return BeforeValidator(partial(_prepare_opaque, max_length=max_length))


Username: TypeAlias = Annotated[
    str,
    _single_line(USERNAME_MAX),
    Field(min_length=1, max_length=USERNAME_MAX),
]

PasswordInput: TypeAlias = Annotated[
    str,
    _opaque(PASSWORD_MAX),
    Field(
        min_length=8,
        max_length=PASSWORD_MAX,
        pattern=app_config.auth.password_pattern,
    ),
]

# Bearer tokens are opaque credentials. Bound them, reject NUL, and otherwise
# preserve the exact byte-for-byte string the client supplied.
AuthTokenInput: TypeAlias = Annotated[
    str,
    _opaque(AUTH_TOKEN_MAX),
    Field(min_length=1, max_length=AUTH_TOKEN_MAX),
]

UserAgent: TypeAlias = Annotated[
    str,
    _opaque(USER_AGENT_MAX),
    Field(max_length=USER_AGENT_MAX),
]

StoryTitle: TypeAlias = Annotated[
    str,
    _single_line(TITLE_MAX),
    Field(min_length=1, max_length=TITLE_MAX),
]

ChapterTitle: TypeAlias = Annotated[
    str,
    _single_line(TITLE_MAX),
    Field(min_length=1, max_length=TITLE_MAX),
]

ThreadTitle: TypeAlias = Annotated[
    str,
    _single_line(TITLE_MAX),
    Field(min_length=1, max_length=TITLE_MAX),
]

SceneTitle: TypeAlias = Annotated[
    str,
    _single_line(TITLE_MAX),
    Field(min_length=1, max_length=TITLE_MAX),
]

SearchQuery: TypeAlias = Annotated[
    str,
    _single_line(SEARCH_QUERY_MAX),
    Field(min_length=1, max_length=SEARCH_QUERY_MAX),
]

NotificationMessage: TypeAlias = Annotated[
    str,
    _single_line(NOTIFICATION_MESSAGE_MAX),
    Field(min_length=1, max_length=NOTIFICATION_MESSAGE_MAX),
]

EntityName: TypeAlias = Annotated[
    str,
    _single_line(ENTITY_NAME_MAX),
    Field(min_length=1, max_length=ENTITY_NAME_MAX),
]

SceneTag: TypeAlias = Annotated[
    str,
    _single_line(TAG_MAX),
    Field(
        min_length=1,
        max_length=TAG_MAX,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    ),
]

NarrativeQuestion: TypeAlias = Annotated[
    str,
    _single_line(QUESTION_MAX),
    Field(min_length=1, max_length=QUESTION_MAX),
]

ChatMessage: TypeAlias = Annotated[
    str,
    _multiline(CHAT_MESSAGE_MAX, strip_outer_whitespace=True),
    Field(min_length=1, max_length=CHAT_MESSAGE_MAX),
]

ChapterContent: TypeAlias = Annotated[
    str,
    _multiline(CHAPTER_CONTENT_MAX, strip_outer_whitespace=False),
    Field(max_length=CHAPTER_CONTENT_MAX),
]

StoryContext: TypeAlias = Annotated[
    str,
    _multiline(STORY_CONTEXT_MAX, strip_outer_whitespace=True),
    Field(max_length=STORY_CONTEXT_MAX),
]

SceneQuote: TypeAlias = Annotated[
    str,
    _multiline(SCENE_QUOTE_MAX, strip_outer_whitespace=True),
    Field(min_length=1, max_length=SCENE_QUOTE_MAX),
]

SceneDescription: TypeAlias = Annotated[
    str,
    _multiline(SCENE_DESCRIPTION_MAX, strip_outer_whitespace=True),
    Field(min_length=1, max_length=SCENE_DESCRIPTION_MAX),
]
