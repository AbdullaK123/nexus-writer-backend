from src.data.schemas.scene import Scene, SceneExtraction
from src.service.extraction.service import ExtractionService


def _scene(start_quote: str, end_quote: str) -> Scene:
    return Scene(
        title="Ambiguous scene",
        start_quote=start_quote,
        end_quote=end_quote,
        description="A deliberately adversarial extraction fixture.",
        pov="Mara",
        tension="medium",
        pacing="steady",
        mentioned_entities=["Mara"],
        tags=["test"],
        questions_raised=[],
    )


def _long_content(*parts: str) -> str:
    filler = " ".join(f"word{i}" for i in range(1_050))
    return " ".join((*parts, filler))


def test_rejects_start_anchor_that_occurs_multiple_times(extraction_context) -> None:
    service, _, _, _ = extraction_context
    repeated = "Mara opened the red door."
    end = "The bell stopped ringing."
    content = _long_content(repeated, "middle", repeated, end)
    extraction = SceneExtraction(scenes=[_scene(repeated, end)])

    errors = service._validate_extraction(extraction, content)

    assert errors, (
        "an anchor that occurs more than once is not a stable scene boundary; "
        "using str.find() silently binds model output to the first occurrence"
    )


def test_rejects_end_anchor_that_occurs_multiple_times(extraction_context) -> None:
    service, _, _, _ = extraction_context
    start = "Mara opened the red door."
    repeated = "The bell stopped ringing."
    content = _long_content(start, repeated, "middle", repeated)
    extraction = SceneExtraction(scenes=[_scene(start, repeated)])

    errors = service._validate_extraction(extraction, content)

    assert errors, (
        "ambiguous end anchors can make a valid-looking extraction point at the wrong scene range"
    )


def test_rejects_identical_start_and_end_anchor(extraction_context) -> None:
    service, _, _, _ = extraction_context
    anchor = "Mara looked up."
    content = _long_content(anchor)
    extraction = SceneExtraction(scenes=[_scene(anchor, anchor)])

    errors = service._validate_extraction(extraction, content)

    assert errors, "a zero-width semantic scene range must never be accepted as a valid extraction"
