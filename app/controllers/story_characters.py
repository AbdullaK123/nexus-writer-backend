from fastapi import APIRouter, Depends, Query
from app.schemas.character import CharacterArcResponse, CharacterInconsistencyResponse, CharacterKnowledgeResponse, CharacterResponse
from app.services.character import CharacterService, get_character_service
from app.services.auth import get_current_user
from app.models import User


router = APIRouter()


@router.get("/", response_model=CharacterResponse)
async def get_characters(
    story_id: str,
    current_user: User = Depends(get_current_user),
    character_service: CharacterService = Depends(get_character_service)
) -> CharacterResponse:
    return await character_service.get_all_characters(
        story_id=story_id,
        user_id=current_user.id
    )


@router.get("/{character_name}/arc", response_model=CharacterArcResponse)
async def get_character_arc(
    story_id: str,
    character_name: str,
    current_user: User = Depends(get_current_user),
    character_service: CharacterService = Depends(get_character_service)
) -> CharacterArcResponse:
    return await character_service.get_character_arc(
        character_name=character_name,
        story_id=story_id,
        user_id=current_user.id
    )


@router.get("/{character_name}/knowledge", response_model=CharacterKnowledgeResponse)
async def get_character_knowledge(
    story_id: str,
    character_name: str,
    chapter_number: int = Query(..., ge=1, description="Cumulative knowledge up to this chapter"),
    current_user: User = Depends(get_current_user),
    character_service: CharacterService = Depends(get_character_service)
) -> CharacterKnowledgeResponse:
    return await character_service.get_knowledge_at_chapter(
        character_name=character_name,
        story_id=story_id,
        user_id=current_user.id,
        chapter_number=chapter_number
    )


@router.get("/{character_name}/inconsistencies", response_model=CharacterInconsistencyResponse)
async def get_character_inconsistencies(
    story_id: str,
    character_name: str,
    current_user: User = Depends(get_current_user),
    character_service: CharacterService = Depends(get_character_service)
) -> CharacterInconsistencyResponse:
    return await character_service.get_inconsistency_report(
        story_id=story_id,
        user_id=current_user.id,
        character_name=character_name
    )
