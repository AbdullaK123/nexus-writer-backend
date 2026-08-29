from src.data.schemas.extraction import Scene, SceneExtraction
from src.service.extraction.service import ExtractionService


def make_scene(start: str, end: str, *, title: str = "Scene") -> Scene:
    return Scene(
        title=title,
        start_quote=start,
        end_quote=end,
        description="A deliberately adversarial scene boundary test.",
        pov="Mara",
        tension="medium",
        pacing="steady",
        mentioned_entities=["Mara"],
        tags=["test"],
        questions_raised=[],
    )


def long_content(body: str) -> str:
    return (("padding " * 1000) + body).strip()


def test_repeated_start_anchor_is_rejected_as_ambiguous(extraction_service: ExtractionService):
    content = long_content(
        "THE DOOR OPENED. Mara crossed the room. THE DOOR OPENED. "
        "She crossed the courtyard. THE END."
    )
    extraction = SceneExtraction(
        scenes=[make_scene("THE DOOR OPENED.", "THE END.")]
    )

    errors = extraction_service._validate_extraction(extraction, content)

    assert any("ambiguous" in error.lower() for error in errors), (
        "a boundary quote that occurs more than once cannot identify a unique persisted scene range"
    )


def test_repeated_end_anchor_is_rejected_as_ambiguous(extraction_service: ExtractionService):
    content = long_content(
        "START. Mara crossed the room. THE BELL RANG. "
        "She crossed the courtyard. THE BELL RANG."
    )
    extraction = SceneExtraction(
        scenes=[make_scene("START.", "THE BELL RANG.")]
    )

    errors = extraction_service._validate_extraction(extraction, content)

    assert any("ambiguous" in error.lower() for error in errors), (
        "persisted end anchors must resolve to exactly one location in the chapter"
    )


def test_identical_start_and_end_anchor_is_rejected(extraction_service: ExtractionService):
    content = long_content("UNIQUE MARKER. Mara waited in silence.")
    extraction = SceneExtraction(
        scenes=[make_scene("UNIQUE MARKER.", "UNIQUE MARKER.")]
    )

    errors = extraction_service._validate_extraction(extraction, content)

    assert errors, "a scene cannot collapse to the same boundary anchor"


def test_scene_whose_end_precedes_start_is_rejected(extraction_service: ExtractionService):
    content = long_content("END FIRST. filler filler filler START LATER.")
    extraction = SceneExtraction(
        scenes=[make_scene("START LATER.", "END FIRST.")]
    )

    errors = extraction_service._validate_extraction(extraction, content)

    assert any("before" in error.lower() for error in errors)


def test_overlapping_scene_ranges_are_rejected(extraction_service: ExtractionService):
    content = long_content(
        "A START. one two three A END. B START. four five B END."
    )
    extraction = SceneExtraction(
        scenes=[
            make_scene("A START.", "B START.", title="First"),
            make_scene("A END.", "B END.", title="Second"),
        ]
    )

    errors = extraction_service._validate_extraction(extraction, content)

    assert any("non-overlapping" in error.lower() for error in errors)
