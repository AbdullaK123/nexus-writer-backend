from sqlmodel.ext.asyncio.session import AsyncSession
from app.models import FrequencyType, Target, Story
from typing import Optional, Dict
from sqlmodel import select
from app.schemas import UpdateTargetRequest, CreateTargetRequest, TargetResponse
from fastapi import HTTPException, status, Depends
from app.core.database import get_db



class TargetProvider:

    def __init__(self, db: AsyncSession):
        self.db = db

    # create a target
    async def create_target(
        self,
        story_id: str,
        user_id: str,
        payload: CreateTargetRequest
    ) -> TargetResponse:
        
        story = await self.db.get(Story, story_id)

        if story is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story not found"
            )
        
        if story.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the story owner can create targets for it"
            )
        
        target = await self.get_target_by_story_id_and_frequency(story_id, user_id, payload.frequency)

        if target:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A target with that frequency already exists"
            )
        
        target_to_create = Target(
            story_id=story_id,
            user_id=user_id,
            **payload.model_dump()
        )
        self.db.add(target_to_create)
        await self.db.commit()

        return TargetResponse(
            quota=target_to_create.quota,
            frequency=target_to_create.frequency,
            from_date=target_to_create.from_date,
            to_date=target_to_create.to_date,
            story_id=story_id,
            target_id=target_to_create.id
        )


    # get by story_id and frequency
    async def get_target_by_story_id_and_frequency(
        self, 
        story_id: str, 
        user_id: str,
        frequency: FrequencyType
    ) -> Optional[TargetResponse]:
        
        target_query = (
            select(Target)
            .where(
                Target.story_id == story_id,
                Target.user_id == user_id,
                Target.frequency == frequency
            )
        )

        target = (await self.db.exec(target_query)).first()

        return TargetResponse(
            quota=target.quota,
            frequency=target.frequency,
            from_date=target.from_date,
            to_date=target.to_date,
            story_id=story_id,
            target_id=target.id
        ) if target else None

    # update
    async def update_target(
        self,
        story_id: str,
        target_id: str,
        user_id: str,
        payload: UpdateTargetRequest
    ) -> TargetResponse:
        
        target = await self.db.get(Target, target_id)

        if target is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target not found"
            )
        
        story = await self.db.get(Story, story_id)
            
        if story is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story not found"
            )
        
        if story.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the story owner can update targets for it"
            )
        

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(target, field, value)

        await self.db.commit()

        return TargetResponse(
            quota=target.quota,
            frequency=target.frequency,
            from_date=target.from_date,
            to_date=target.to_date,
            story_id=target.story_id,
            target_id=target.id
        )

    # delete
    async def delete_target(
        self,
        story_id: str,
        user_id: str,
        target_id: str
    ) -> Dict[str, str]:
        
        target = await self.db.get(Target, target_id)

        if target is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target not found"
            )
        
        story = await self.db.get(Story, story_id)
            
        if story is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story not found"
            )
        
        if story.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the story owner can update targets for it"
            )

        await self.db.delete(target)
        await self.db.commit()

        return {
            "message": "Successfully deleted target"
        }


def get_target_provider(
    db: AsyncSession = Depends(get_db)
) -> TargetProvider:
    return TargetProvider(db)