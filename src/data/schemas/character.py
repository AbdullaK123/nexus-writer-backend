from typing import List, Optional

from pydantic import BaseModel

from src.data.schemas.extraction import Character, CharacterImportance, CharacterRoster, CharacterStatus


class CharacterQuery(BaseModel):
    name: Optional[str] = None
    aliases: Optional[str] = None
    importance: Optional[CharacterImportance] = None
    status: Optional[CharacterStatus] = None
    description: Optional[str] = None
    key_relationships: Optional[str] = None
    tags: Optional[str] = None


class CharacterListResponse(BaseModel):
    roster: Optional[List[Character]] = []
    is_stale: Optional[bool] = False