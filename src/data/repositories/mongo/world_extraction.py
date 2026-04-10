from typing import Any, Dict, List, Optional
from pymongo.asynchronous.database import AsyncDatabase
from src.infrastructure.utils.retry import retry_mongo


class WorldExtractionRepo:

    def __init__(self, db: AsyncDatabase):
        self.collection = db.world_extractions

    @retry_mongo
    async def get_contradictions(self, story_id: str, user_id: str) -> List[dict]:
        cursor = await self.collection.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$unwind": "$facts"},
            {"$group": {
                "_id": {"entity": "$facts.entity", "attribute": "$facts.attribute"},
                "facts": {
                    "$push": {
                        "chapter_number": "$chapter_number",
                        "chapter_id": "$chapter_id",
                        "value": "$facts.value"
                    }
                },
                "distinct_values": {"$addToSet": "$facts.value"}
            }},
            {"$match": {"$expr": {"$gt": [{"$size": "$distinct_values"}, 1]}}}
        ])
        return [doc async for doc in cursor]

    @retry_mongo
    async def get_entity_registry(
        self, story_id: str, user_id: str,
        entities: Optional[List[str]] = None,
    ) -> List[dict]:
        match_filter: Dict[str, Any] = {"story_id": story_id, "user_id": user_id}
        if entities:
            match_filter["facts.entity"] = {"$in": entities}

        cursor = await self.collection.aggregate([
            {"$match": match_filter},
            {"$unwind": "$facts"},
            {"$sort": {"chapter_number": -1}},
            {"$group": {
                "_id": {"entity": "$facts.entity", "attribute": "$facts.attribute"},
                "value": {"$first": "$facts.value"}
            }},
            {"$group": {
                "_id": "$_id.entity",
                "facts": {
                    "$push": {
                        "attribute": "$_id.attribute",
                        "value": "$value"
                    }
                }
            }}
        ])
        return [doc async for doc in cursor]

    @retry_mongo
    async def get_entity_timeline(self, story_id: str, user_id: str, entity: str) -> List[dict]:
        cursor = await self.collection.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$unwind": "$facts"},
            {"$match": {"facts.entity": entity}},
            {"$group": {
                "_id": {"chapter_number": "$chapter_number", "chapter_id": "$chapter_id"},
                "facts": {
                    "$push": {
                        "attribute": "$facts.attribute",
                        "value": "$facts.value"
                    }
                }
            }},
            {"$sort": {"_id.chapter_number": 1}}
        ])
        return [doc async for doc in cursor]

    @retry_mongo
    async def get_fact_density(self, story_id: str, user_id: str) -> List[dict]:
        cursor = await self.collection.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$unwind": "$facts"},
            {"$group": {
                "_id": {"chapter_number": "$chapter_number", "chapter_id": "$chapter_id"},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id.chapter_number": 1}}
        ])
        return [doc async for doc in cursor]

    # Write operations

    @retry_mongo
    async def save_extraction(
        self, chapter_id: str, story_id: str, user_id: str,
        chapter_number: int, extraction_data: dict
    ) -> None:
        meta = {
            "chapter_id": chapter_id,
            "story_id": story_id,
            "user_id": user_id,
            "chapter_number": chapter_number,
        }
        await self.collection.replace_one(
            {"chapter_id": chapter_id},
            {**meta, **extraction_data},
            upsert=True,
        )

    @retry_mongo
    async def delete_by_chapter(self, chapter_id: str) -> None:
        await self.collection.delete_one({"chapter_id": chapter_id})
