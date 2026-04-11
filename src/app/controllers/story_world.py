from fastapi import APIRouter, Depends, Query
from dependency_injector.wiring import inject, Provide
from src.infrastructure.di.containers import ApplicationContainer
from typing import List, Optional
from src.data.schemas.world import (
    ContradictionResponse, EntityFactResponse, EntityTimelineResponse,
    StoryFactCountsResponse, WorldConsistencyReport,
)
from src.service.analysis.world import WorldConsistencyService
from src.service.auth.service import get_current_user
from src.data.models import User


router = APIRouter()


@router.get("/contradictions", response_model=ContradictionResponse)
@inject
async def get_contradictions(
    story_id: str,
    current_user: User = Depends(get_current_user),
    world_service: WorldConsistencyService = Depends(Provide[ApplicationContainer.world_service]),
) -> ContradictionResponse:
    return await world_service.get_contradictions(
        story_id=story_id,
        user_id=current_user.id,
    )


@router.get("/entities", response_model=List[EntityFactResponse])
@inject
async def get_entity_registry(
    story_id: str,
    current_user: User = Depends(get_current_user),
    world_service: WorldConsistencyService = Depends(Provide[ApplicationContainer.world_service]),
    entities: Optional[List[str]] = Query(default=None),
) -> List[EntityFactResponse]:
    return await world_service.get_entity_registry(
        story_id=story_id,
        user_id=current_user.id,
        entities=entities,
    )


@router.get("/entities/{entity}/timeline", response_model=EntityTimelineResponse)
@inject
async def get_entity_timeline(
    story_id: str,
    entity: str,
    current_user: User = Depends(get_current_user),
    world_service: WorldConsistencyService = Depends(Provide[ApplicationContainer.world_service]),
) -> EntityTimelineResponse:
    return await world_service.get_entity_timeline(
        story_id=story_id,
        user_id=current_user.id,
        entity=entity,
    )


@router.get("/fact-density", response_model=StoryFactCountsResponse)
@inject
async def get_fact_density(
    story_id: str,
    current_user: User = Depends(get_current_user),
    world_service: WorldConsistencyService = Depends(Provide[ApplicationContainer.world_service]),
) -> StoryFactCountsResponse:
    return await world_service.get_fact_density(
        story_id=story_id,
        user_id=current_user.id,
    )


@router.get("/report", response_model=WorldConsistencyReport)
@inject
async def get_world_consistency_report(
    story_id: str,
    current_user: User = Depends(get_current_user),
    world_service: WorldConsistencyService = Depends(Provide[ApplicationContainer.world_service]),
) -> WorldConsistencyReport:
    return await world_service.get_consistency_report(
        story_id=story_id,
        user_id=current_user.id,
    )
