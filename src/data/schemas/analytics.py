from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from src.data.schemas._base import ApiModel
from datetime import datetime


class Metric(BaseModel):
    name: str
    value: float | int 


class AnalyticsSuggestionExtraction(BaseModel):
    headline: str
    analysis: str
    status: Literal["healthy", "worth-watching", "needs-your-attention", "not-available"]


class AnalyticsSuggestionResponse(ApiModel):
    story_id: str
    story_title: str
    generated_at: datetime
    metric: Metric
    suggestion: AnalyticsSuggestionExtraction


class PlotThread(BaseModel):
    name: str 
    chapter_started: int
    chapter_ended: Optional[int] = None
    chapter_last_touched: int
    status: Literal["open", "resolved", "unknown"]

class PlotThreadsExtraction(BaseModel):
    threads: Optional[List[PlotThread]] = []

class PlotThreadsResponse(ApiModel):
    story_id: str
    story_title: str
    path_array: List[str]
    generated_at: datetime
    extraction: PlotThreadsExtraction


class Act(BaseModel):
    number: Literal[1, 2, 3, 4]
    chapter_started: int
    chapter_ended: Optional[int] = None
    current_chapter: Optional[int] = None

class ActSegmentationExtraction(BaseModel):
    acts: Optional[List[Act]] = []

class ActSegmentationResponse(ApiModel):
    story_id: str
    story_title: str
    path_array: List[str]
    generated_at: datetime
    extraction: ActSegmentationExtraction


class Contradiction(BaseModel):
    headline: str
    report: str
    relevant_chapters: List[int]

class ContradictionExtraction(BaseModel):
    contradictions: Optional[List[Contradiction]] = []

class ContradictionResponse(ApiModel):
    story_id: str
    story_title: str
    path_array: List[str]
    generated_at: datetime
    extraction: ContradictionExtraction


class Entity(BaseModel):
    type: Literal["place", "faction", "concept", "system", "character", "other"]
    name: str
    chapter_first_appeared: int
    chapter_last_touched: int 

class EntityLedgerExtraction(BaseModel):
    entities: Optional[List[Entity]]

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