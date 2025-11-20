from pydantic import BaseModel, Field
from typing import List
from app.agents.models.nodes import Character
from app.agents.models.relationships import CharacterRelationship

class CharacterExtractionResult(BaseModel):
    characters: List[Character] = Field(
        description="List of characters extracted from the chapter."
    )
    relationships: List[CharacterRelationship] = Field(
        description="List of relationships extracted from the chapter."
    )