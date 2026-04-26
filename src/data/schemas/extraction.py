from pydantic import Field, BaseModel
from typing import Literal, List, Optional

class Scene(BaseModel):
    title: str = Field(description="A short descriptive title for the scene.")
    start_quote: str = Field(description="A short VERBATIM quote from the chapter marking where the scene begins.")
    end_quote: str = Field(description="A short VERBATIM quote from the chapter marking where the scene ends.")
    description: str = Field(description="A 3-4 sentence synopsis of what happened in the scene")
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