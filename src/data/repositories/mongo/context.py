from typing import List
from pymongo.asynchronous.database import AsyncDatabase
from src.infrastructure.utils.retry import retry_mongo


class ContextRepo:

    def __init__(self, db: AsyncDatabase):
        self.collection = db.chapter_contexts

    @retry_mongo
    async def get_preceding_contexts(
        self, story_id: str, before_chapter_number: int
    ) -> List[dict]:
        return await self.collection.find(
            {
                "story_id": story_id,
                "chapter_number": {"$lt": before_chapter_number},
            }
        ).sort("chapter_number", -1).to_list(length=50)

    # Write operations

    @retry_mongo
    async def save_context(
        self, chapter_id: str, story_id: str, user_id: str,
        chapter_number: int, context_data: dict
    ) -> None:
        meta = {
            "chapter_id": chapter_id,
            "story_id": story_id,
            "user_id": user_id,
            "chapter_number": chapter_number,
        }
        await self.collection.replace_one(
            {"chapter_id": chapter_id},
            {**meta, **context_data},
            upsert=True,
        )

    @retry_mongo
    async def delete_by_chapter(self, chapter_id: str) -> None:
        await self.collection.delete_one({"chapter_id": chapter_id})
