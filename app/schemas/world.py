from sqlmodel import SQLModel
from typing import List, Optional

from app.ai.models.world import Fact


class ContradictingFact(SQLModel):
    chapter_number: int
    chapter_id: str
    value: str

class Contradiction(SQLModel):
    entity: str
    attribute: str
    occurrences: Optional[List[ContradictingFact]] = []

class ContradictionResponse(SQLModel):
    contradictions: Optional[List[Contradiction]] = []

class EntityFact(SQLModel):
    attribute: str 
    value: str

class EntityFactResponse(SQLModel):
    entity: str
    facts: Optional[List[EntityFact]] = []

class ChapterEntityFacts(SQLModel):
    chapter_number: int 
    chapter_id: str
    facts: Optional[List[EntityFact]] = []

class EntityTimelineResponse(SQLModel):
    chapter_facts: Optional[List[ChapterEntityFacts]] = []

class ChapterFactCount(SQLModel):
    chapter_number: int 
    chapter_id: str 
    count: int

class StoryFactCountsResponse(SQLModel):
    counts: Optional[List[ChapterFactCount]] = []

class WorldConsistencyReport(SQLModel):
    story_id: str 
    report: str = ""




