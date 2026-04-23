from enum import StrEnum
from typing import List, Optional
from pydantic import BaseModel
from src.data.schemas.extraction import Entity, EntityImportance


class EntityType(StrEnum):
    PLACES = "places"
    FACTIONS = "factions"
    TECHNOLOGIES = "technologies"
    HISTORICAL_EVENTS = "historical_events"
    OTHER = "other"
    CULTURAL_FACTS = "cultural_facts"


class EntityQuery(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    importance: Optional[EntityImportance] = None
    tags: Optional[List[str]] = None
    search_term: Optional[str] = None


class EntityListResponse(BaseModel):
    entities: Optional[List[Entity]] = []
    num_found: Optional[int] = 0
    is_stale: Optional[bool] = False