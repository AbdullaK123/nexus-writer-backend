from typing import Dict, List, Optional
from pydantic import BaseModel
from app.ai.models.character import Character



class CharacterResponse(BaseModel):
    characters: Optional[List[Character]] = []


class ChapterEmotionalState(BaseModel):
    chapter_id: str
    chapter_number: int
    emotional_state: str

class ChapterGoals(BaseModel):
    chapter_id: str
    chapter_number: int
    goals: List[str]

class ChapterKnowledgeGained(BaseModel):
    chapter_id: str
    chapter_number: int
    knowledge_gained: List[str]

class CharacterArcResponse(BaseModel):
    character_name: str
    emotional_states: List[ChapterEmotionalState] = []
    goals: List[ChapterGoals] = []
    knowledge_gained: List[ChapterKnowledgeGained] = []


class CharacterKnowledgeResponse(BaseModel):
    character_name: str
    chapter_number: int
    knowledge: List[str] = []

class CharacterInconsistencyResponse(BaseModel):
    character_name: str
    report: str = ""