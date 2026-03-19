from typing import List
from fastapi import APIRouter, Depends, Query
from app.schemas.plot import (
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
from app.services.plot import PlotService, get_plot_service
from app.services.plot_tracker import PlotTrackerService, get_plot_tracker_service
from app.services.auth import get_current_user
from app.models import User


router = APIRouter()


@router.get("/threads", response_model=PlotThreadsResponse)
async def get_unresolved_plot_threads(
    story_id: str,
    current_user: User = Depends(get_current_user),
    plot_service: PlotService = Depends(get_plot_service)
) -> PlotThreadsResponse:
    return await plot_service.get_all_unresolved_plot_threads(
        user_id=current_user.id,
        story_id=story_id
    )


@router.get("/questions", response_model=StoryQuestionsResponse)
async def get_unanswered_questions(
    story_id: str,
    current_user: User = Depends(get_current_user),
    plot_service: PlotService = Depends(get_plot_service)
) -> StoryQuestionsResponse:
    return await plot_service.get_all_unanswered_story_questions(
        user_id=current_user.id,
        story_id=story_id
    )


@router.get("/setups", response_model=SetupResponse)
async def get_setups_with_no_payoff(
    story_id: str,
    current_user: User = Depends(get_current_user),
    plot_service: PlotService = Depends(get_plot_service)
) -> SetupResponse:
    return await plot_service.get_all_setups_with_no_payoffs(
        user_id=current_user.id,
        story_id=story_id
    )

@router.get("/deus-ex-machinas", response_model=DeusExMachinaResponse)
async def get_deus_ex_machinas(
    story_id: str,
    current_user: User = Depends(get_current_user),
    plot_service: PlotService = Depends(get_plot_service)
) -> DeusExMachinaResponse:
    return await plot_service.get_all_deus_ex_machinas(
        user_id=current_user.id,
        story_id=story_id
    )

@router.get("/report", response_model=PlotStructuralReportResponse)
async def get_plot_report(
    story_id: str,
    current_user: User = Depends(get_current_user),
    plot_service: PlotService = Depends(get_plot_service)
) -> PlotStructuralReportResponse:
    return await plot_service.get_structural_report(
        story_id=story_id,
        user_id=current_user.id
    )


@router.get("/thread-timeline", response_model=ThreadTimelineResponse)
async def get_thread_timeline(
    story_id: str,
    thread_name: str = Query(...),
    current_user: User = Depends(get_current_user),
    service: PlotTrackerService = Depends(get_plot_tracker_service),
) -> ThreadTimelineResponse:
    return await service.get_thread_timeline(
        story_id=story_id,
        user_id=current_user.id,
        thread_name=thread_name,
    )


@router.get("/dormant-threads", response_model=DormantThreadsResponse)
async def get_dormant_threads(
    story_id: str,
    min_gap: int = Query(3, ge=1),
    current_user: User = Depends(get_current_user),
    service: PlotTrackerService = Depends(get_plot_tracker_service),
) -> DormantThreadsResponse:
    return await service.get_dormant_threads(
        story_id=story_id,
        user_id=current_user.id,
        min_gap=min_gap,
    )


@router.get("/event-density", response_model=EventDensityResponse)
async def get_event_density(
    story_id: str,
    current_user: User = Depends(get_current_user),
    service: PlotTrackerService = Depends(get_plot_tracker_service),
) -> EventDensityResponse:
    return await service.get_event_density(
        story_id=story_id,
        user_id=current_user.id,
    )


@router.get("/setup-payoff-map", response_model=List[SetupPayoffMap])
async def get_setup_payoff_map(
    story_id: str,
    current_user: User = Depends(get_current_user),
    service: PlotTrackerService = Depends(get_plot_tracker_service),
) -> List[SetupPayoffMap]:
    return await service.get_setup_payoff_map(
        story_id=story_id,
        user_id=current_user.id,
    )


@router.get("/density", response_model=PlotDensityResponse)
async def get_plot_density(
    story_id: str,
    current_user: User = Depends(get_current_user),
    service: PlotTrackerService = Depends(get_plot_tracker_service),
) -> PlotDensityResponse:
    return await service.get_plot_density(
        story_id=story_id,
        user_id=current_user.id,
    )


@router.get("/rhythm-report", response_model=PlotRhythmReportResponse)
async def get_plot_rhythm_report(
    story_id: str,
    current_user: User = Depends(get_current_user),
    service: PlotTrackerService = Depends(get_plot_tracker_service),
) -> PlotRhythmReportResponse:
    return await service.get_plot_rhythm_report(
        story_id=story_id,
        user_id=current_user.id,
    )
