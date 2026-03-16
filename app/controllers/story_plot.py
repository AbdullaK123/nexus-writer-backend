from fastapi import APIRouter, Depends
from app.schemas.plot import DeusExMachinaResponse, PlotStructuralReportResponse, PlotThreadsResponse, SetupResponse, StoryQuestionsResponse
from app.services.plot import PlotService, get_plot_service
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
