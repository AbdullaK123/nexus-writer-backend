import pytest
from pydantic import ValidationError

from src.data.schemas.extraction import Scene
from src.shared.text_types import (
    SCENE_DESCRIPTION_MAX,
    SCENE_QUOTE_MAX,
    TITLE_MAX,
)


def scene_payload(**overrides):
    payload = {
        "title": "A valid scene",
        "start_quote": "The door opened.",
        "end_quote": "Mara left.",
        "description": "Mara enters, speaks with Vale, and leaves.",
        "pov": "Mara",
        "tension": "medium",
        "pacing": "steady",
        "mentioned_entities": ["Mara", "Captain Vale"],
        "tags": ["character-development"],
        "questions_raised": ["Why did Vale refuse?"],
    }
    payload.update(overrides)
    return payload


@pytest.mark.parametrize(
    "field,value",
    [
        ("title", "safe\x00poison"),
        ("start_quote", "safe\x00poison"),
        ("end_quote", "safe\x00poison"),
        ("description", "safe\x00poison"),
        ("pov", "safe\x00poison"),
    ],
)
def test_generated_scene_text_rejects_nul_before_database(field, value) -> None:
    with pytest.raises(ValidationError, match="NUL characters are not allowed"):
        Scene(**scene_payload(**{field: value}))


@pytest.mark.parametrize(
    "field,value,limit",
    [
        ("title", "x" * (TITLE_MAX + 1), TITLE_MAX),
        ("start_quote", "x" * (SCENE_QUOTE_MAX + 1), SCENE_QUOTE_MAX),
        ("end_quote", "x" * (SCENE_QUOTE_MAX + 1), SCENE_QUOTE_MAX),
        ("description", "x" * (SCENE_DESCRIPTION_MAX + 1), SCENE_DESCRIPTION_MAX),
    ],
)
def test_generated_scene_text_is_bounded_before_persistence(field, value, limit) -> None:
    with pytest.raises(ValidationError, match=f"at most {limit}"):
        Scene(**scene_payload(**{field: value}))


def test_generated_scene_tags_must_obey_canonical_kebab_case() -> None:
    with pytest.raises(ValidationError):
        Scene(**scene_payload(tags=["Plot Twist!!!", "  betrayal  "]))


def test_generated_entity_names_reject_invisible_formatting() -> None:
    scene = Scene(**scene_payload(mentioned_entities=["Ma\u200bra", "Captain Vale"]))

    assert scene.mentioned_entities == ["Mara", "Captain Vale"]
