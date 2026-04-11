from fastapi import APIRouter, Depends, Query
from dependency_injector.wiring import inject, Provide
from src.infrastructure.di.containers import ApplicationContainer
from typing import Optional
from src.data.schemas.structure import (
    SceneIndexResponse, WeakScenesResponse, SceneTypeDistributionResponse,
    POVBalanceResponse, PacingCurveResponse, StructuralArcResponse,
    ThemeDistributionResponse, EmotionalBeatsResponse, DevelopmentalReportResponse,
)
from src.service.analysis.structure import StructureService
from src.service.auth.service import get_current_user
from src.data.models import User


router = APIRouter()


@router.get("/scenes", response_model=SceneIndexResponse)
@inject
async def get_scene_index(
    story_id: str,
    scene_type: Optional[str] = Query(default=None),
    pov: Optional[str] = Query(default=None),
    location: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
    structure_service: StructureService = Depends(Provide[ApplicationContainer.structure_service]),
) -> SceneIndexResponse:
    return await structure_service.get_scene_index(
        story_id=story_id,
        user_id=current_user.id,
        scene_type=scene_type,
        pov=pov,
        location=location,
    )


@router.get("/scenes/weak", response_model=WeakScenesResponse)
@inject
async def get_weak_scenes(
    story_id: str,
    current_user: User = Depends(get_current_user),
    structure_service: StructureService = Depends(Provide[ApplicationContainer.structure_service]),
) -> WeakScenesResponse:
    return await structure_service.get_weak_scenes(
        story_id=story_id,
        user_id=current_user.id,
    )


@router.get("/scenes/distribution", response_model=SceneTypeDistributionResponse)
@inject
async def get_scene_type_distribution(
    story_id: str,
    current_user: User = Depends(get_current_user),
    structure_service: StructureService = Depends(Provide[ApplicationContainer.structure_service]),
) -> SceneTypeDistributionResponse:
    return await structure_service.get_scene_type_distribution(
        story_id=story_id,
        user_id=current_user.id,
    )


@router.get("/pov-balance", response_model=POVBalanceResponse)
@inject
async def get_pov_balance(
    story_id: str,
    current_user: User = Depends(get_current_user),
    structure_service: StructureService = Depends(Provide[ApplicationContainer.structure_service]),
) -> POVBalanceResponse:
    return await structure_service.get_pov_balance(
        story_id=story_id,
        user_id=current_user.id,
    )


@router.get("/pacing", response_model=PacingCurveResponse)
@inject
async def get_pacing_curve(
    story_id: str,
    current_user: User = Depends(get_current_user),
    structure_service: StructureService = Depends(Provide[ApplicationContainer.structure_service]),
) -> PacingCurveResponse:
    return await structure_service.get_pacing_curve(
        story_id=story_id,
        user_id=current_user.id,
    )


@router.get("/arc", response_model=StructuralArcResponse)
@inject
async def get_structural_arc(
    story_id: str,
    current_user: User = Depends(get_current_user),
    structure_service: StructureService = Depends(Provide[ApplicationContainer.structure_service]),
) -> StructuralArcResponse:
    return await structure_service.get_structural_arc(
        story_id=story_id,
        user_id=current_user.id,
    )


@router.get("/themes", response_model=ThemeDistributionResponse)
@inject
async def get_theme_tracker(
    story_id: str,
    current_user: User = Depends(get_current_user),
    structure_service: StructureService = Depends(Provide[ApplicationContainer.structure_service]),
) -> ThemeDistributionResponse:
    return await structure_service.get_theme_tracker(
        story_id=story_id,
        user_id=current_user.id,
    )


@router.get("/emotional-beats", response_model=EmotionalBeatsResponse)
@inject
async def get_emotional_beat_report(
    story_id: str,
    current_user: User = Depends(get_current_user),
    structure_service: StructureService = Depends(Provide[ApplicationContainer.structure_service]),
) -> EmotionalBeatsResponse:
    return await structure_service.get_emotional_beat_report(
        story_id=story_id,
        user_id=current_user.id,
    )


@router.get("/report", response_model=DevelopmentalReportResponse)
@inject
async def get_developmental_report(
    story_id: str,
    current_user: User = Depends(get_current_user),
    structure_service: StructureService = Depends(Provide[ApplicationContainer.structure_service]),
) -> DevelopmentalReportResponse:
    return await structure_service.get_developmental_report(
        story_id=story_id,
        user_id=current_user.id,
    )
