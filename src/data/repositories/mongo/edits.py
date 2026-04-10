from datetime import datetime, timezone
from typing import List, Optional
from pymongo.asynchronous.database import AsyncDatabase
from src.infrastructure.utils.retry import retry_mongo


class EditsRepo:

    def __init__(self, db: AsyncDatabase):
        self.collection = db.chapter_edits

    @retry_mongo
    async def get_by_chapter(self, chapter_id: str) -> Optional[dict]:
        return await self.collection.find_one({"chapter_id": chapter_id})

    # Write operations

    @retry_mongo
    async def save_edits(
        self, chapter_id: str, story_id: str, user_id: str,
        chapter_number: int, edits: List[dict],
    ) -> None:
        await self.collection.replace_one(
            {"chapter_id": chapter_id},
            {
                "chapter_id": chapter_id,
                "story_id": story_id,
                "user_id": user_id,
                "chapter_number": chapter_number,
                "edits": edits,
                "last_generated_at": datetime.now(timezone.utc),
                "is_stale": False,
            },
            upsert=True,
        )

    @retry_mongo
    async def mark_stale(self, chapter_id: str) -> None:
        await self.collection.update_one(
            {"chapter_id": chapter_id},
            {"$set": {"is_stale": True}},
            upsert=True,
        )

    @retry_mongo
    async def delete_by_chapter(self, chapter_id: str) -> None:
        await self.collection.delete_one({"chapter_id": chapter_id})
