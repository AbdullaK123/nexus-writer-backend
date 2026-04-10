from pydantic import BaseModel
from typing import List, Optional

from src.service.ai.models.world import Fact


class ContradictingFact(BaseModel):
    chapter_number: int
    chapter_id: str
    value: str

class Contradiction(BaseModel):
    entity: str
    attribute: str
    occurrences: Optional[List[ContradictingFact]] = []

class ContradictionResponse(BaseModel):
    contradictions: Optional[List[Contradiction]] = []

class EntityFact(BaseModel):
    attribute: str 
    value: str

class EntityFactResponse(BaseModel):
    entity: str
    facts: Optional[List[EntityFact]] = []

class ChapterEntityFacts(BaseModel):
    chapter_number: int 
    chapter_id: str
    facts: Optional[List[EntityFact]] = []

class EntityTimelineResponse(BaseModel):
    chapter_facts: Optional[List[ChapterEntityFacts]] = []

class ChapterFactCount(BaseModel):
    chapter_number: int 
    chapter_id: str 
    count: int

class StoryFactCountsResponse(BaseModel):
    counts: Optional[List[ChapterFactCount]] = []

class WorldConsistencyReport(BaseModel):
    story_id: str 
    report: str = ""
