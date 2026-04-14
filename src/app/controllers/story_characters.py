from fastapi import APIRouter, Depends, Query
from dependency_injector.wiring import inject, Provide
from src.app.di.containers import ApplicationContainer
from src.data.schemas.character import (
    CharacterAppearancesResponse,
    CharacterArcResponse,
    CharacterDensityResponse,
    CharacterGoalsResponse,
    CharacterInconsistencyResponse,
    CharacterIntroductionResponse,
    CharacterKnowledgeMapResponse,
    CharacterKnowledgeResponse,
    CharacterResponse,
    CastManagementReportResponse,
)
from src.service.analysis.character import CharacterService
from src.service.analysis.character_tracker import CharacterTrackerService
from src.app.dependencies import get_current_user
from src.data.models import User


router = APIRouter()


@router.get("/", response_model=CharacterResponse)
@inject
async def get_characters(
    story_id: str,
    current_user: User = Depends(get_current_user),
    character_service: CharacterService = Depends(Provide[ApplicationContainer.character_service])
) -> CharacterResponse:
    return await character_service.get_all_characters(
        story_id=story_id,
        user_id=current_user.id
    )


@router.get("/{character_name}/arc", response_model=CharacterArcResponse)
@inject
async def get_character_arc(
    story_id: str,
    character_name: str,
    current_user: User = Depends(get_current_user),
    character_service: CharacterService = Depends(Provide[ApplicationContainer.character_service])
) -> CharacterArcResponse:
    return await character_service.get_character_arc(
        character_name=character_name,
        story_id=story_id,
        user_id=current_user.id
    )


@router.get("/{character_name}/knowledge", response_model=CharacterKnowledgeResponse)
@inject
async def get_character_knowledge(
    story_id: str,
    character_name: str,
    chapter_number: int = Query(..., ge=1, description="Cumulative knowledge up to this chapter"),
    current_user: User = Depends(get_current_user),
    character_service: CharacterService = Depends(Provide[ApplicationContainer.character_service])
) -> CharacterKnowledgeResponse:
    return await character_service.get_knowledge_at_chapter(
        character_name=character_name,
        story_id=story_id,
        user_id=current_user.id,
        chapter_number=chapter_number
    )


@router.get("/{character_name}/inconsistencies", response_model=CharacterInconsistencyResponse)
@inject
async def get_character_inconsistencies(
    story_id: str,
    character_name: str,
    current_user: User = Depends(get_current_user),
    character_service: CharacterService = Depends(Provide[ApplicationContainer.character_service])
) -> CharacterInconsistencyResponse:
    return await character_service.get_inconsistency_report(
        story_id=story_id,
        user_id=current_user.id,
        character_name=character_name
    )


@router.get("/presence-map", response_model=CharacterAppearancesResponse)
@inject
async def get_character_presence_map(
    story_id: str,
    current_user: User = Depends(get_current_user),
    service: CharacterTrackerService = Depends(Provide[ApplicationContainer.character_tracker_service]),
) -> CharacterAppearancesResponse:
    return await service.get_character_presence_map(
        story_id=story_id,
        user_id=current_user.id,
    )


@router.get("/introduction-rate", response_model=CharacterIntroductionResponse)
@inject
async def get_character_introduction_rate(
    story_id: str,
    current_user: User = Depends(get_current_user),
    service: CharacterTrackerService = Depends(Provide[ApplicationContainer.character_tracker_service]),
) -> CharacterIntroductionResponse:
    return await service.get_character_introduction_rate(
        story_id=story_id,
        user_id=current_user.id,
    )


@router.get("/density", response_model=CharacterDensityResponse)
@inject
async def get_cast_density(
    story_id: str,
    current_user: User = Depends(get_current_user),
    service: CharacterTrackerService = Depends(Provide[ApplicationContainer.character_tracker_service]),
) -> CharacterDensityResponse:
    return await service.get_cast_density(
        story_id=story_id,
        user_id=current_user.id,
    )


@router.get("/cast-report", response_model=CastManagementReportResponse)
@inject
async def get_cast_management_report(
    story_id: str,
    current_user: User = Depends(get_current_user),
    service: CharacterTrackerService = Depends(Provide[ApplicationContainer.character_tracker_service]),
) -> CastManagementReportResponse:
    return await service.get_cast_management_report(
        story_id=story_id,
        user_id=current_user.id,
    )


@router.get("/{character_name}/goals", response_model=CharacterGoalsResponse)
@inject
async def get_goal_evolution(
    story_id: str,
    character_name: str,
    current_user: User = Depends(get_current_user),
    service: CharacterTrackerService = Depends(Provide[ApplicationContainer.character_tracker_service]),
) -> CharacterGoalsResponse:
    return await service.get_goal_evolution(
        story_id=story_id,
        user_id=current_user.id,
        character_name=character_name,
    )


@router.get("/{character_name}/knowledge-map", response_model=CharacterKnowledgeMapResponse)
@inject
async def get_knowledge_asymmetry(
    story_id: str,
    character_name: str,
    chapter_number: int = Query(..., ge=1, description="Cumulative knowledge up to this chapter"),
    current_user: User = Depends(get_current_user),
    service: CharacterTrackerService = Depends(Provide[ApplicationContainer.character_tracker_service]),
) -> CharacterKnowledgeMapResponse:
    return await service.get_knowledge_asymmetry(
        story_id=story_id,
        user_id=current_user.id,
        character_name=character_name,
        chapter_number=chapter_number,
    )
