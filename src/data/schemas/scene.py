from datetime import datetime
from pydantic import Field, BaseModel, ConfigDict, field_validator
from typing import Literal, List, Optional
from src.data.schemas._base import ApiModel


# ─── LLM I/O models (used as JSON schema for structured generation) ─────────


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
    """LLM output container — the bag of scenes extracted from one chapter.
    Not persisted directly; the service explodes it into per-scene rows."""
    scenes: List[Scene] = Field(default_factory=list)


# ─── DB row model ──────────────────────────────────────────────────────────


class SceneRow(BaseModel):
    """One row from the `scene` table. Repository return type.

    Embedding columns are nullable: extraction populates every column except
    `embedding` / `embedding_model` / `embedded_at`. A separate worker
    fills those in once the vector is generated.
    """
    model_config = ConfigDict(from_attributes=True)

    id: str
    chapter_id: str
    story_id: str
    user_id: str
    position: int
    title: str
    start_quote: str
    end_quote: str
    description: str
    tension: Literal["low", "medium", "high"]
    pacing: Literal["slow", "steady", "fast"]
    mentioned_entities: List[str]
    tags: List[str]
    questions_raised: List[str]
    # `embedding` itself isn't modelled here — pgvector returns it as text;
    # callers that need the raw vector should fetch via a dedicated method.
    embedding_model: Optional[str] = None
    embedded_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class SceneSearchResult(SceneRow):
    """A `SceneRow` plus a hybrid-search relevance score.

    Returned by `SceneRepository.search_scenes`. The score is the Reciprocal
    Rank Fusion sum of the BM25 and vector-similarity ranks (higher = more
    relevant). Values are not comparable across queries — they're only
    meaningful for ordering within one result set.
    """
    score: float

class SceneSearchRequest(ApiModel):
    """Body for POST /stories/{story_id}/search.

    `k` is the cap on returned hits; `candidate_pool` is how many FTS/vector
    rows feed the RRF fusion before truncation. Both are optional — when
    omitted, the service falls back to `search.default_k` /
    `search.default_candidate_pool` from config. Most callers should leave
    them unset.
    """
    query: str = Field(min_length=1, max_length=500)
    k: int | None = Field(default=None, ge=1, le=50)
    candidate_pool: int | None = Field(default=None, ge=1, le=500)
    tension: Literal["low", "medium", "high"] | None = None
    pacing: Literal["slow", "steady", "fast"] | None = None
    # Open-vocabulary array filters. Empty list normalises to None so it
    # behaves identically to "omit the field" — otherwise an empty list
    # under the && operator would match zero rows, a confusing footgun.
    tags: List[str] | None = None
    mentioned_entities: List[str] | None = None
    chapter_ids: List[str] | None = None

    @field_validator("tags", "mentioned_entities", "chapter_ids", mode="after")
    @classmethod
    def _empty_to_none(cls, v: List[str] | None) -> List[str] | None:
        return v or None

class SceneSearchListResponse(ApiModel):
    """Wrapper so the API returns an object, not a bare list (easier to
    extend with paging/metadata later without breaking clients)."""
    results: List["SceneSearchResponse"]


class SceneSearchResponse(ApiModel):
    """API-shaped projection of a hybrid-search hit.

    Mirrors `SceneSearchResult` but excludes internal columns the client
    doesn't need (user_id, position, embedded_at, embedding_model). Use
    `from_result` to convert from the repository return type.
    """

    id: str
    chapter_id: str
    story_id: str
    title: str
    description: str
    start_quote: str
    end_quote: str
    tension: Literal["low", "medium", "high"]
    pacing: Literal["slow", "steady", "fast"]
    mentioned_entities: List[str]
    tags: List[str]
    questions_raised: List[str]
    score: float
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_result(cls, result: "SceneSearchResult") -> "SceneSearchResponse":
        return cls.model_validate(result, from_attributes=True)


# ─── Vocabulary listing (tags / entities) ────────────────────────────────────


class VocabularyItem(ApiModel):
    """One (value, count) pair from the per-story tag/entity vocabulary.
    Sorted by count desc on the way out so the most common labels come
    first — useful both for UI surfacing and for letting the agent prioritise
    high-signal filter values."""
    value: str
    count: int


class VocabularyListResponse(ApiModel):
    items: List[VocabularyItem]
