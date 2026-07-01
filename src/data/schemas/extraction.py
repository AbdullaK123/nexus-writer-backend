from datetime import datetime
from pydantic import Field, BaseModel, ConfigDict
from typing import Literal, List

from src.data.schemas._base import ApiModel


class Scene(BaseModel):
    title: str = Field(description="A short descriptive title for the scene.")
    start_quote: str = Field(description="A short VERBATIM quote from the chapter marking where the scene begins.")
    end_quote: str = Field(description="A short VERBATIM quote from the chapter marking where the scene ends.")
    description: str = Field(description="A 3-4 sentence synopsis of what happened in the scene")
    pov: str = Field(description="The POV character of the scene. It MUST correspond to an entity in the mentioned_entities field.")
    tension: Literal["low", "medium", "high"] = Field(
        description="""
        The dramatic tension of the scene. 
        'low' = calm, expository, or reflective beats with little immediate stakes; 
        'medium' = active conflict, rising stakes, meaningful character friction, or unresolved questions driving the scene forward; 
        'high' = climactic confrontation, danger, irreversible decisions, or emotional peaks where the outcome materially changes the story.
        """
    )
    pacing: Literal["slow", "steady", "fast"] = Field(
        description="""
        The narrative pacing of the scene — how quickly story time and events progress relative to the prose.
        'slow' = lingering moments, introspection, detailed description, or extended dialogue where little plot advances per paragraph;
        'steady' = balanced forward motion: events, dialogue, and reflection alternate at a consistent rhythm that moves the story without rushing;
        'fast' = rapid succession of actions or revelations, short sentences/exchanges, time compression, or escalating beats that propel the reader through the scene quickly.
        """
    )
    mentioned_entities: List[str] = Field(
        description="""
        A list of named entities explicitly referenced in the scene — characters (by name or unambiguous epithet), distinct locations, organizations/factions, and named objects or artifacts that carry narrative weight.
        Include each entity once, using its most specific canonical name as it appears in the chapter (e.g. 'Captain Vale' rather than 'the captain'; 'the Obsidian Spire' rather than 'the tower').
        Exclude generic nouns ('the man', 'a city'), pronouns, and incidental background mentions that have no bearing on the scene's events.
        Exclude anything that is not likely to have downstream importance to the story
        """
    )
    tags: List[str] = Field(
        description="""
        A short list (typically 3-7) of lowercase keyword tags that categorize the scene for later retrieval and filtering.
        Cover any of: scene function ('exposition', 'inciting-incident', 'turning-point', 'climax', 'denouement'), content/mood ('combat', 'romance', 'betrayal', 'reunion', 'flashback', 'foreshadowing', 'comic-relief'), and structural role ('worldbuilding', 'character-development', 'plot-revelation').
        Use kebab-case, single concept per tag, no duplicates, and prefer reusable categorical labels over scene-specific descriptions (e.g. 'betrayal', not 'vale-betrays-mira').
        """
    )
    questions_raised: List[str] = Field(
        description="""
        A short list (typically 0-5) of concrete narrative questions the scene opens, sharpens, or leaves unresolved in the reader's mind — the hooks that create forward pull.
        Phrase each as a complete question from the reader's perspective (e.g. 'Will Hannah be able to convince Mindoir's governor to evacuate?', 'What is the Silent Ones' true objective?', 'Can Rael survive the assault on Earth?').
        Include only questions that are genuinely live at the end of the scene — newly raised, escalated, or still open. Exclude questions the scene definitively answers, generic thematic musings, and meta-questions about the author's craft.
        Prefer specific, plot- or character-grounded questions over vague ones ('Will Mark recover from his trauma?' over 'What will happen next?'). Return an empty list for purely connective scenes that raise no new questions.
        """
    )

class SceneExtraction(BaseModel):
    scenes: List[Scene] = Field(default_factory=list)


class ExtractionRow(BaseModel):
    """One row from the `extraction` table. Repository return type."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    chapter_id: str
    extraction_type: str
    needs_reextraction: bool
    data: SceneExtraction
    created_at: datetime
    updated_at: datetime

class PulseDimension(BaseModel):
    """
    A high-level editorial assessment of one dimension of the story:
    characters, plot, structure, or world.

    The assessment identifies the single most consequential pattern visible
    across the ordered scene synopses. It evaluates broad narrative health
    and state only, without making claims about prose-level execution.
    """

    label: Literal[
        "healthy",
        "watch",
        "needs-attention",
        "unavailable",
    ] = Field(
        description="""
        The current health classification for this story dimension.

        Use 'healthy' when the dimension functions coherently and no
        significant manuscript-wide concern is evident.

        Use 'watch' when there is a plausible developing imbalance or weakness
        that deserves the author's attention but does not substantially impair
        the story.

        Use 'needs-attention' when a clear and consequential pattern across the
        manuscript warrants author review.

        Use 'unavailable' only when the input lacks coherent narrative scenes,
        is unrelated to story analysis, is gibberish, or is too sparse to
        support a responsible assessment.
        """
    )

    headline: str = Field(
        description="""
        A concise, story-specific headline expressing the single most important
        high-level finding for this dimension.

        State the actual narrative pattern rather than a generic judgment.
        Prefer a clear observation such as 'The supporting cast disappears as
        the invasion escalates' over labels such as 'Character development
        needs work.'

        When the label is 'unavailable', state that this dimension's pulse is
        unavailable.
        """
    )

    report: str = Field(
        description="""
        A short executive report explaining the headline in 2-3 sentences.

        Describe the dominant manuscript-wide pattern, support it with concrete
        story-specific observations from the scene synopses, and briefly explain
        why it matters. Remain at the level of characters, plot, structure, or
        world appropriate to the current call.

        Do not provide a list, detailed scene critique, prescriptive rewrite
        advice, unsupported speculation, or claims about prose-level qualities
        that cannot be determined from scene synopses.

        When the label is 'unavailable', briefly explain why the supplied
        context cannot support the assessment.
        """
    )

class BookPulseResponse(ApiModel):
    """The complete high-level editorial pulse for a story."""

    characters: PulseDimension
    plot: PulseDimension
    structure: PulseDimension
    world: PulseDimension

INSUFFICIENT_CONTEXT = BookPulseResponse(
    characters=PulseDimension(
        label="unavailable",
        headline="Characters pulse is unavailable.",
        report=(
            "The supplied scenes do not contain enough character activity "
            "to support a meaningful assessment. More narrative content "
            "is needed before character health can be evaluated."
        ),
    ),
    plot=PulseDimension(
        label="unavailable",
        headline="Plot pulse is unavailable.",
        report=(
            "There are too few scenes to identify plot-level patterns. "
            "A responsible assessment requires enough material to observe "
            "cause-and-effect progression across the manuscript."
        ),
    ),
    structure=PulseDimension(
        label="unavailable",
        headline="Structure pulse is unavailable.",
        report=(
            "Structural assessment requires a sequence of scenes long enough "
            "to exhibit pacing, rhythm, and arc shape. The current input "
            "is too sparse for that analysis."
        ),
    ),
    world=PulseDimension(
        label="unavailable",
        headline="World pulse is unavailable.",
        report=(
            "The supplied context does not contain enough setting detail "
            "or world-building to support an assessment of this dimension."
        ),
    ),
)