from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from src.data.schemas._base import ApiModel
from datetime import datetime


# class Metric(BaseModel):
#     name: str
#     value: float | int


class AnalyticsSuggestionExtraction(BaseModel):
    headline: str = Field(
        description="A concise, story-specific headline stating the most important editorial implication of the supplied metric."
    )
    analysis: str = Field(
        description="""
        A short editorial analysis explaining what the supplied metric suggests about the story and why it matters.
        Ground the analysis in the metric and available story context, distinguish observation from inference, and avoid generic advice or unsupported claims.
        When the status is 'not-available', briefly explain why the metric cannot support a responsible interpretation.
        """
    )
    status: Literal["healthy", "worth-watching", "needs-your-attention", "not-available"] = Field(
        description="""
        The editorial significance of the metric.
        'healthy' = the metric reflects a coherent or well-balanced story pattern with no meaningful concern;
        'worth-watching' = the metric suggests a plausible developing imbalance that deserves monitoring but is not yet a clear problem;
        'needs-your-attention' = the metric reveals a clear, consequential pattern that warrants author review;
        'not-available' = the metric or supplied context is missing, invalid, or insufficient for a responsible assessment.
        """
    )


class AnalyticsSuggestionResponse(ApiModel):
    story_id: str
    story_title: str
    generated_at: datetime
    suggestion: AnalyticsSuggestionExtraction


class PlotThread(BaseModel):
    name: str = Field(
        description="""
        A concise canonical name for one distinct, narratively significant plot thread.
        Name the underlying objective, conflict, mystery, promise, or unresolved dramatic question rather than a single event, scene, or chapter.
        Use the same name for later developments of the same thread and do not split one continuous thread into near-duplicates.
        """
    )
    chapter_started: int = Field(
        description="The 1-based chapter number where the plot thread is first clearly established or becomes narratively active."
    )
    chapter_ended: Optional[int] = Field(
        default=None,
        description="The 1-based chapter number where the plot thread is definitively resolved or closed; null when it remains open or its resolution cannot be determined."
    )
    chapter_last_touched: int = Field(
        description="The latest 1-based chapter number that meaningfully develops, complicates, advances, or resolves the thread; incidental mentions do not count."
    )
    status: Literal["open", "resolved", "unknown"] = Field(
        description="""
        The current state of the plot thread.
        'open' = the story still presents the thread as active, unresolved, or awaiting consequence;
        'resolved' = the story supplies a clear payoff, answer, conclusion, or closure for the thread;
        'unknown' = the available evidence is too ambiguous to determine whether the thread remains active or has been resolved.
        """
    )


class PlotThreadsExtraction(BaseModel):
    threads: Optional[List[PlotThread]] = Field(
        default_factory=list,
        description="""
        All distinct, narratively significant plot threads visible in the supplied story context.
        Return each thread once using a stable canonical name, order threads by the chapter where they begin, and exclude fleeting events that create no continuing objective, conflict, mystery, promise, or consequence.
        Return an empty list when no meaningful plot threads can be identified.
        """
    )


class PlotThreadsResponse(ApiModel):
    story_id: str
    story_title: str
    path_array: List[str]
    generated_at: datetime
    extraction: PlotThreadsExtraction


class Act(BaseModel):
    number: Literal[1, 2, 3, 4] = Field(
        description="The sequential act number assigned to this broad structural phase of the story."
    )
    chapter_started: int = Field(
        description="The 1-based chapter number where this act begins, inclusive."
    )
    chapter_ended: Optional[int] = Field(
        default=None,
        description="The 1-based chapter number where this act ends, inclusive; null only when this is the currently unfinished act."
    )
    current_chapter: Optional[int] = Field(
        default=None,
        description="The latest available 1-based chapter number within this act when it is still in progress; null for completed acts."
    )


class ActSegmentationExtraction(BaseModel):
    acts: Optional[List[Act]] = Field(
        default_factory=list,
        description="""
        The story's broad structural phases in chronological order.
        Acts must be sequential, contiguous, and non-overlapping, with boundaries placed at meaningful changes in objective, conflict, stakes, direction, or narrative function.
        Do not force the story into four acts when the supplied material supports fewer, especially when the manuscript is unfinished. Return an empty list when no responsible segmentation can be made.
        """
    )


class ActSegmentationResponse(ApiModel):
    story_id: str
    story_title: str
    path_array: List[str]
    generated_at: datetime
    extraction: ActSegmentationExtraction


class Contradiction(BaseModel):
    headline: str = Field(
        description="A concise, story-specific headline naming the two facts, states, or continuity claims that appear incompatible."
    )
    report: str = Field(
        description="""
        A short factual report explaining the apparent contradiction and the evidence on each side.
        State what the story establishes in the relevant chapters and why the claims cannot both be true as currently presented.
        Do not treat intentional deception, character belief, uncertainty, mystery, changed circumstances, or information later corrected by the story as contradictions.
        """
    )
    relevant_chapters: List[int] = Field(
        description="A sorted list of unique 1-based chapter numbers containing the direct evidence needed to verify the apparent contradiction."
    )


class ContradictionExtraction(BaseModel):
    contradictions: Optional[List[Contradiction]] = Field(
        default_factory=list,
        description="""
        High-confidence factual or continuity contradictions supported by the supplied story context.
        Include only conflicts that can be checked against direct evidence in the cited chapters; exclude subjective interpretation, deliberate lies, unreliable narration, unresolved mysteries, and details that can coexist or change over time.
        Return an empty list when no defensible contradictions are present.
        """
    )


class ContradictionResponse(ApiModel):
    story_id: str
    story_title: str
    path_array: List[str]
    generated_at: datetime
    extraction: ContradictionExtraction


class Entity(BaseModel):
    type: Literal["place", "faction", "concept", "system", "character", "other"] = Field(
        description="""
        The entity's narrative category.
        'place' = a named physical location;
        'faction' = an organization, government, group, institution, or collective actor;
        'concept' = a named abstract idea, doctrine, event, phenomenon, or piece of lore;
        'system' = a named technology, process, framework, mechanism, or structured set of rules;
        'character' = an individual person, creature, intelligence, or person-like agent;
        'other' = a significant named entity that does not responsibly fit another category.
        """
    )
    name: str = Field(
        description="The entity's most specific canonical name as used by the story; merge aliases and repeated references to the same entity into one ledger entry."
    )
    chapter_first_appeared: int = Field(
        description="The 1-based chapter number where the entity first appears or is first explicitly introduced."
    )
    chapter_last_touched: int = Field(
        description="The latest 1-based chapter number where the entity appears, acts, changes, is discussed meaningfully, or otherwise affects the narrative; incidental mentions do not count."
    )


class EntityLedgerExtraction(BaseModel):
    entities: Optional[List[Entity]] = Field(
        description="""
        A deduplicated ledger of named entities with continuing or meaningful narrative importance across the supplied story context.
        Return one entry per canonical entity, order entries by first appearance and then name, and exclude generic nouns, unnamed background elements, and incidental details unlikely to matter downstream.
        Return an empty list when no qualifying entities are present.
        """
    )


class EntityLedgerResponse(ApiModel):
    story_id: str
    story_title: str
    path_array: List[str]
    generated_at: datetime
    extraction: EntityLedgerExtraction


class CastStatisticsRow(BaseModel):
    character: str
    scene_count: int
    word_count: int


class CastStatisticsResponse(ApiModel):
    story_id: str
    story_title: str
    statistics: List[CastStatisticsRow]


class CoOccurenceStatisticsRow(BaseModel):
    character_a: str
    character_b: str
    scene_count: int
    word_count: int


class CoOccurenceStatisticsResponse(ApiModel):
    story_id: str
    story_title: str
    statistics: List[CoOccurenceStatisticsRow]


class CharacterStatisticsRow(BaseModel):
    chapter_id: str
    chapter_number: int
    pov: str
    scene_count: int
    word_count: int


class CharacterStatisticsResponse(ApiModel):
    story_id: str
    story_title: str
    statistics: List[CharacterStatisticsRow]


class SceneLengthDistributionRow(BaseModel):
    bin: str
    count: int


class SceneLengthDistributionResponse(ApiModel):
    story_id: str
    story_title: str
    distribution: List[SceneLengthDistributionRow]


class TensionCurveRow(BaseModel):
    chapter_id: str
    chapter_number: int
    avg_tension: float


class PacingCurveRow(BaseModel):
    chapter_id: str
    chapter_number: int
    avg_pacing: float


class TensionAndPacingCurveResponse(ApiModel):
    story_id: str
    story_title: str
    tension_curve: List[TensionCurveRow]
    pacing_curve: List[PacingCurveRow]
