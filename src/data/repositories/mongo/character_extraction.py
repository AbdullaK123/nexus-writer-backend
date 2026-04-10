from typing import List, Optional
from pymongo.asynchronous.database import AsyncDatabase
from src.infrastructure.utils.retry import retry_mongo


class CharacterExtractionRepo:

    def __init__(self, db: AsyncDatabase):
        self.collection = db.character_extractions

    @retry_mongo
    async def get_latest_per_character(self, story_id: str, user_id: str) -> List[dict]:
        cursor = await self.collection.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$unwind": "$characters"},
            {"$sort": {"chapter_number": -1}},
            {"$group": {
                "_id": "$characters.name",
                "character": {"$first": "$characters"}
            }}
        ])
        return [doc async for doc in cursor]

    @retry_mongo
    async def get_character_arc(self, story_id: str, user_id: str, character_name: str) -> List[dict]:
        cursor = await self.collection.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$unwind": "$characters"},
            {"$match": {"characters.name": character_name}},
            {"$sort": {"chapter_number": 1}},
            {"$group": {
                "_id": None,
                "emotional_states": {
                    "$push": {
                        "chapter_id": "$chapter_id",
                        "chapter_number": "$chapter_number",
                        "emotional_state": "$characters.emotional_state"
                    }
                },
                "goals": {
                    "$push": {
                        "chapter_id": "$chapter_id",
                        "chapter_number": "$chapter_number",
                        "goals": "$characters.goals"
                    }
                },
                "knowledge_gained": {
                    "$push": {
                        "chapter_id": "$chapter_id",
                        "chapter_number": "$chapter_number",
                        "knowledge_gained": "$characters.knowledge_gained"
                    }
                }
            }}
        ])
        return await cursor.to_list(length=1)

    @retry_mongo
    async def get_cumulative_knowledge(
        self, story_id: str, user_id: str, character_name: str, up_to_chapter: int
    ) -> List[dict]:
        cursor = await self.collection.aggregate([
            {"$match": {
                "story_id": story_id,
                "user_id": user_id,
                "chapter_number": {"$lte": up_to_chapter}
            }},
            {"$unwind": "$characters"},
            {"$match": {"characters.name": character_name}},
            {"$group": {
                "_id": None,
                "all_knowledge": {"$push": "$characters.knowledge_gained"},
            }},
            {"$project": {
                "knowledge": {
                    "$reduce": {
                        "input": "$all_knowledge",
                        "initialValue": [],
                        "in": {"$concatArrays": ["$$value", "$$this"]}
                    }
                }
            }}
        ])
        return await cursor.to_list(length=1)

    @retry_mongo
    async def get_presence_map(self, story_id: str, user_id: str) -> List[dict]:
        cursor = await self.collection.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$unwind": "$characters"},
            {"$sort": {"chapter_number": 1}},
            {"$group": {
                "_id": "$characters.name",
                "appearances": {
                    "$push": {
                        "chapter_number": "$chapter_number",
                        "chapter_id": "$chapter_id"
                    }
                }
            }}
        ])
        return [doc async for doc in cursor]

    @retry_mongo
    async def get_introduction_rate(self, story_id: str, user_id: str) -> List[dict]:
        cursor = await self.collection.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$unwind": "$characters"},
            {"$match": {"characters.is_new": True}},
            {"$group": {
                "_id": {"chapter_id": "$chapter_id", "chapter_number": "$chapter_number"},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id.chapter_number": 1}}
        ])
        return [doc async for doc in cursor]

    @retry_mongo
    async def get_goal_evolution(
        self, story_id: str, user_id: str, character_name: str
    ) -> List[dict]:
        cursor = await self.collection.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id, "characters.name": character_name}},
            {"$unwind": "$characters"},
            {"$match": {"characters.name": character_name}},
            {"$project": {
                "_id": 0,
                "chapter_id": 1,
                "chapter_number": 1,
                "goals": "$characters.goals",
            }},
            {"$sort": {"chapter_number": 1}}
        ])
        return [doc async for doc in cursor]

    @retry_mongo
    async def get_knowledge_asymmetry(
        self, story_id: str, user_id: str, character_name: str, up_to_chapter: int
    ) -> List[dict]:
        cursor = await self.collection.aggregate([
            {"$match": {
                "story_id": story_id,
                "user_id": user_id,
                "chapter_number": {"$lte": up_to_chapter},
                "characters.name": character_name,
            }},
            {"$unwind": "$characters"},
            {"$match": {"characters.name": character_name}},
            {"$project": {
                "_id": 0,
                "chapter_id": 1,
                "chapter_number": 1,
                "knowledge": "$characters.knowledge_gained",
            }},
            {"$sort": {"chapter_number": 1}}
        ])
        return [doc async for doc in cursor]

    @retry_mongo
    async def get_cast_density(self, story_id: str, user_id: str) -> List[dict]:
        cursor = await self.collection.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$project": {
                "_id": 0,
                "chapter_id": 1,
                "chapter_number": 1,
                "characters_present": {"$size": {"$ifNull": ["$characters", []]}},
            }},
            {"$sort": {"chapter_number": 1}}
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
