from fastapi import APIRouter, Depends, Query
from dependency_injector.wiring import inject, Provide
from src.infrastructure.di.containers import ApplicationContainer
from typing import Optional
from src.service.target.service import TargetService
from src.service.auth.service import get_current_user
from src.data.models import User, FrequencyType
from src.data.schemas.target import TargetResponse, CreateTargetRequest, UpdateTargetRequest, TargetListResponse


router = APIRouter()


@router.post("/", response_model=TargetResponse)
@inject
async def create_target(
    story_id: str,
    payload: CreateTargetRequest,
    current_user: User = Depends(get_current_user),
    target_service: TargetService = Depends(Provide[ApplicationContainer.target_service])
) -> TargetResponse:
    return await target_service.create_target(
        story_id,
        current_user.id,
        payload
    )

@router.get("/")
@inject
async def get_targets(
    story_id: str,
    frequency: Optional[FrequencyType] = Query(default=None),
    current_user: User = Depends(get_current_user),
    target_service: TargetService = Depends(Provide[ApplicationContainer.target_service])
):
    """
    Get targets for a story.
    - If frequency is provided, returns a single target (or null)
    - If frequency is not provided, returns all targets for the story
    """
    if frequency:
        return await target_service.get_target_by_story_id_and_frequency(
            story_id,
            current_user.id,
            frequency
        )
    else:
        targets = await target_service.get_all_targets_by_story_id(
            story_id,
            current_user.id
        )
        return TargetListResponse(targets=targets)

@router.put("/{target_id}", response_model=TargetResponse)
@inject
async def update_target(
    story_id: str,
    target_id: str,
    payload: UpdateTargetRequest,
    current_user: User = Depends(get_current_user),
    target_service: TargetService = Depends(Provide[ApplicationContainer.target_service])
) -> TargetResponse:
    return await target_service.update_target(
        story_id,
        target_id,
        current_user.id,
        payload
    )

@router.delete("/{target_id}")
@inject
async def delete_target(
    story_id: str,
    target_id: str,
    current_user: User = Depends(get_current_user),
    target_service: TargetService = Depends(Provide[ApplicationContainer.target_service])
) -> dict:
    return await target_service.delete_target(
        story_id,
        current_user.id,
        target_id
    )
