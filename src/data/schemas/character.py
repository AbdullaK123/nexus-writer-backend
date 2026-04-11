from typing import List, Optional
from pydantic import BaseModel
from src.data.models.ai.character import Character



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


class CharacterAppearance(BaseModel):
    chapter_number: int 
    chapter_id: str


class CharacterAppearanceMap(BaseModel):
    character_name: str 
    appearances: Optional[List[CharacterAppearance]] = []

class CharacterAppearancesResponse(BaseModel):
    maps: Optional[List[CharacterAppearanceMap]] = []

class CharacterIntroductionCount(BaseModel):
    chapter_number: int 
    chapter_id: str 
    characters_introduced: int 

class CharacterIntroductionResponse(BaseModel):
    counts: Optional[List[CharacterIntroductionCount]] = []

class CharacterGoalsResponse(BaseModel):
    character_name: str
    goals: Optional[List[ChapterGoals]] = []

class CharacterKnowledgeMap(BaseModel):
    chapter_number: int 
    chapter_id: str 
    knowledge: Optional[List[str]] = []

class CharacterKnowledgeMapResponse(BaseModel):
    character_name: str 
    maps: Optional[List[CharacterKnowledgeMap]] = []

class ChapterCharacterDensity(BaseModel):
    chapter_number: int 
    chapter_id: str 
    characters_present: int 

class CharacterDensityResponse(BaseModel):
    counts: Optional[List[ChapterCharacterDensity]] = []

class CastManagementReportResponse(BaseModel):
    story_id: str
    report: str = ""
