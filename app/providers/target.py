from sqlmodel.ext.asyncio.session import AsyncSession
from app.models import FrequencyType, Target
from typing import Optional, Dict
from sqlmodel import select
from app.schemas import UpdateChapterRequest, TargetResponse, CreateChapterRequest
from fastapi import HTTPException, status



class TargetProvider:

    def __init__(self, db: AsyncSession):
        self.db = db

    # create a target
    async def create_target(
        self,
        story_id: str,
        user_id: str,
        payload: CreateChapterRequest
    ) -> Target:
        
        target_to_create = Target(
            story_id=story_id,
            user_id=user_id,
            **payload.model_dump()
        )
        self.db.add(target_to_create)
        await self.db.commit()

        return target_to_create


    # get by story_id and frequency
    async def get_target_by_story_id_and_frequency(
        self, 
        story_id: str, 
        user_id: str,
        frequency: FrequencyType
    ) -> Optional[Target]:
        
        target_query = (
            select(Target)
            .where(
                Target.story_id == story_id,
                Target.user_id == user_id,
                Target.frequency == frequency
            )
        )

        target = (await self.db.execute(target_query)).scalar_one_or_none()

        return target

    # update
    async def update_target(
        self,
        target_id: str,
        user_id: str,
        payload: UpdateChapterRequest
    ) -> Target:
        
        target_query = (
            select(Target)
            .where(
                Target.id == target_id,
                Target.user_id == user_id
            )
        )

        target_to_update = (await self.db.execute(target_query)).scalar_one_or_none()

        if target_to_update is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target not found"
            )
        
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(target_to_update, field, value)

        await self.db.commit()

        return target_to_update

    # delete
    async def delete_target(
        self,
        user_id: str,
        target_id: str
    ) -> Dict[str, str]:
        
        target_query = (
            select(Target)
            .where(
                Target.id == target_id,
                Target.user_id == user_id
            )
        )

        target_to_delete = (await self.db.execute(target_query)).scalar_one_or_none()

        if target_to_delete is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target not found"
            )

        await self.db.delete(target_to_delete)
        await self.db.commit()

        return {
            "message": "Successfully deleted target"
        }
