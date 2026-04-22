from typing import List, Literal, Optional

from pydantic import BaseModel

from src.data.schemas.extraction import Character, CharacterArcType, CharacterImportance, CharacterRoster, CharacterStatus


class CharacterQuery(BaseModel):
    importance: Optional[CharacterImportance] = None
    status: Optional[CharacterStatus] = None
    tags: Optional[List[str]] = None
    aliases: Optional[List[str]] = None
    key_relationships: Optional[List[str]] = None
    search_term: Optional[str] = None
    arc_type: Optional[CharacterArcType] = None

class CharacterListResponse(BaseModel):
    roster: Optional[List[Character]] = []
    num_found: Optional[int] = 0
    is_stale: Optional[bool] = False


class ItemWithCount(BaseModel):
    value: str
    count: int

class ItemListResponse(BaseModel):
    items: List[ItemWithCount]



