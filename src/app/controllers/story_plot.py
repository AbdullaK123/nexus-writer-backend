from typing import List
from fastapi import APIRouter, Depends, Query
from dependency_injector.wiring import inject, Provide
from src.infrastructure.di.containers import ApplicationContainer
from src.data.schemas.plot import (
    DeusExMachinaResponse,
    DormantThreadsResponse,
    EventDensityResponse,
    PlotDensityResponse,
    PlotRhythmReportResponse,
    PlotStructuralReportResponse,
    PlotThreadsResponse,
    SetupPayoffMap,
    SetupResponse,
    StoryQuestionsResponse,
    ThreadTimelineResponse,
)
from src.service.analysis.plot import PlotService
from src.service.analysis.plot_tracker import PlotTrackerService
from src.service.auth.service import get_current_user
from src.data.models import User


router = APIRouter()


@router.get("/threads", response_model=PlotThreadsResponse)
@inject
async def get_unresolved_plot_threads(
    story_id: str,
    current_user: User = Depends(get_current_user),
    plot_service: PlotService = Depends(Provide[ApplicationContainer.plot_service])
) -> PlotThreadsResponse:
    return await plot_service.get_all_unresolved_plot_threads(
        user_id=current_user.id,
        story_id=story_id
    )


@router.get("/questions", response_model=StoryQuestionsResponse)
@inject
async def get_unanswered_questions(
    story_id: str,
    current_user: User = Depends(get_current_user),
    plot_service: PlotService = Depends(Provide[ApplicationContainer.plot_service])
) -> StoryQuestionsResponse:
    return await plot_service.get_all_unanswered_story_questions(
        user_id=current_user.id,
        story_id=story_id
    )


@router.get("/setups", response_model=SetupResponse)
@inject
async def get_setups_with_no_payoff(
    story_id: str,
    current_user: User = Depends(get_current_user),
    plot_service: PlotService = Depends(Provide[ApplicationContainer.plot_service])
) -> SetupResponse:
    return await plot_service.get_all_setups_with_no_payoffs(
        user_id=current_user.id,
        story_id=story_id
    )

@router.get("/deus-ex-machinas", response_model=DeusExMachinaResponse)
@inject
async def get_deus_ex_machinas(
    story_id: str,
    current_user: User = Depends(get_current_user),
    plot_service: PlotService = Depends(Provide[ApplicationContainer.plot_service])
) -> DeusExMachinaResponse:
    return await plot_service.get_all_deus_ex_machinas(
        user_id=current_user.id,
        story_id=story_id
    )

@router.get("/report", response_model=PlotStructuralReportResponse)
@inject
async def get_plot_report(
    story_id: str,
    current_user: User = Depends(get_current_user),
    plot_service: PlotService = Depends(Provide[ApplicationContainer.plot_service])
) -> PlotStructuralReportResponse:
    return await plot_service.get_structural_report(
        story_id=story_id,
        user_id=current_user.id
    )


@router.get("/thread-timeline", response_model=ThreadTimelineResponse)
@inject
async def get_thread_timeline(
    story_id: str,
    thread_name: str = Query(...),
    current_user: User = Depends(get_current_user),
    service: PlotTrackerService = Depends(Provide[ApplicationContainer.plot_tracker_service]),
) -> ThreadTimelineResponse:
    return await service.get_thread_timeline(
        story_id=story_id,
        user_id=current_user.id,
        thread_name=thread_name,
    )


@router.get("/dormant-threads", response_model=DormantThreadsResponse)
@inject
async def get_dormant_threads(
    story_id: str,
    min_gap: int = Query(3, ge=1),
    current_user: User = Depends(get_current_user),
    service: PlotTrackerService = Depends(Provide[ApplicationContainer.plot_tracker_service]),
) -> DormantThreadsResponse:
    return await service.get_dormant_threads(
        story_id=story_id,
        user_id=current_user.id,
        min_gap=min_gap,
    )


@router.get("/event-density", response_model=EventDensityResponse)
@inject
async def get_event_density(
    story_id: str,
    current_user: User = Depends(get_current_user),
    service: PlotTrackerService = Depends(Provide[ApplicationContainer.plot_tracker_service]),
) -> EventDensityResponse:
    return await service.get_event_density(
        story_id=story_id,
        user_id=current_user.id,
    )


@router.get("/setup-payoff-map", response_model=List[SetupPayoffMap])
@inject
async def get_setup_payoff_map(
    story_id: str,
    current_user: User = Depends(get_current_user),
    service: PlotTrackerService = Depends(Provide[ApplicationContainer.plot_tracker_service]),
) -> List[SetupPayoffMap]:
    return await service.get_setup_payoff_map(
        story_id=story_id,
        user_id=current_user.id,
    )


@router.get("/density", response_model=PlotDensityResponse)
@inject
async def get_plot_density(
    story_id: str,
    current_user: User = Depends(get_current_user),
    service: PlotTrackerService = Depends(Provide[ApplicationContainer.plot_tracker_service]),
) -> PlotDensityResponse:
    return await service.get_plot_density(
        story_id=story_id,
        user_id=current_user.id,
    )


@router.get("/rhythm-report", response_model=PlotRhythmReportResponse)
@inject
async def get_plot_rhythm_report(
    story_id: str,
    current_user: User = Depends(get_current_user),
    service: PlotTrackerService = Depends(Provide[ApplicationContainer.plot_tracker_service]),
) -> PlotRhythmReportResponse:
    return await service.get_plot_rhythm_report(
        story_id=story_id,
        user_id=current_user.id,
    )
