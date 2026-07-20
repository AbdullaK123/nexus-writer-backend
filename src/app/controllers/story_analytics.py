from fastapi import APIRouter, Depends, Query
from src.app.dependencies.auth import get_current_user
from src.app.dependencies.services import get_analytics_service
from src.data.schemas.analytics import CharacterDashboardResponse, PlotDashboardResponse, StructureDashboardResponse, WorldDashboardResponse
from src.data.schemas.auth import UserRow
from src.service.analytics.service import AnalyticsService


analytics_controller = APIRouter(prefix="/{story_id}/analytics")


@analytics_controller.get("/dashboard/characters")
async def get_character_dashboard(
    story_id: str,
    current_user: UserRow = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> CharacterDashboardResponse:
    return await analytics_service.get_character_dashboard(story_id, current_user.id)

@analytics_controller.get("/dashboard/plot")
async def get_plot_dashboard(
    story_id: str,
    ignore_cache: bool = Query(default=False),
    current_user: UserRow = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> PlotDashboardResponse:
    return await analytics_service.get_plot_dashboard(story_id, current_user.id, ignore_cache)


@analytics_controller.get("/dashboard/structure")
async def get_structure_dashboard(
    story_id: str,
    current_user: UserRow = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> StructureDashboardResponse:
    return await analytics_service.get_structure_dashboard(story_id, current_user.id)

@analytics_controller.get("/dashboard/world")
async def get_world_dashboard(
    story_id: str,
    ignore_cache: bool = Query(default=False),
    current_user: UserRow = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> WorldDashboardResponse:
    return await analytics_service.get_world_dashboard(story_id, current_user.id, ignore_cache)