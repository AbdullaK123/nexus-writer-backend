from typing import Dict, List, Optional
from sqlmodel import SQLModel
from app.ai.models.character import Character



class CharacterResponse(SQLModel):
    characters: Optional[List[Character]] = []


class ChapterEmotionalState(SQLModel):
    chapter_id: str
    chapter_number: int
    emotional_state: str

class ChapterGoals(SQLModel):
    chapter_id: str
    chapter_number: int
    goals: List[str]

class ChapterKnowledgeGained(SQLModel):
    chapter_id: str
    chapter_number: int
    knowledge_gained: List[str]

class CharacterArcResponse(SQLModel):
    character_name: str
    emotional_states: List[ChapterEmotionalState] = []
    goals: List[ChapterGoals] = []
    knowledge_gained: List[ChapterKnowledgeGained] = []


class CharacterKnowledgeResponse(SQLModel):
    character_name: str
    chapter_number: int
    knowledge: List[str] = []

class CharacterInconsistencyResponse(SQLModel):
    character_name: str
    report: str = ""