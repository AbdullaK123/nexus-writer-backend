from typing import Any, Dict, List, Optional
from pymongo.asynchronous.database import AsyncDatabase
from src.infrastructure.utils.retry import retry_mongo


class StructureExtractionRepo:

    def __init__(self, db: AsyncDatabase):
        self.collection = db.structure_extractions

    @retry_mongo
    async def get_scenes(
        self, story_id: str, user_id: str,
        scene_filter: Optional[Dict[str, Any]] = None,
    ) -> List[dict]:
        match_filter = scene_filter or {}
        cursor = await self.collection.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$unwind": "$scenes"},
            {"$match": match_filter},
            {"$project": {
                "_id": 0,
                "chapter_id": 1,
                "chapter_number": 1,
                "scene": "$scenes"
            }},
            {"$sort": {"chapter_number": 1}}
        ])
        return [doc async for doc in cursor]

    @retry_mongo
    async def get_weak_scenes(self, story_id: str, user_id: str) -> List[dict]:
        cursor = await self.collection.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$unwind": "$scenes"},
            {"$match": {
                "$or": [
                    {"scenes.goal": ""},
                    {"scenes.conflict": ""},
                    {"scenes.outcome": ""}
                ]
            }},
            {"$group": {
                "_id": {"chapter_number": "$chapter_number", "chapter_id": "$chapter_id"},
                "scenes": {
                    "$push": {
                        "type": "$scenes.type",
                        "location": "$scenes.location",
                        "pov": "$scenes.pov",
                        "goal": "$scenes.goal",
                        "conflict": "$scenes.conflict",
                        "outcome": "$scenes.outcome",
                        "word_count": "$scenes.word_count"
                    }
                }
            }},
            {"$sort": {"_id.chapter_number": 1}}
        ])
        return [doc async for doc in cursor]

    @retry_mongo
    async def get_scene_type_counts(self, story_id: str, user_id: str) -> List[dict]:
        cursor = await self.collection.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$unwind": "$scenes"},
            {"$group": {
                "_id": {
                    "chapter_number": "$chapter_number",
                    "chapter_id": "$chapter_id",
                    "type": "$scenes.type"
                },
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id.chapter_number": 1}}
        ])
        return [doc async for doc in cursor]

    @retry_mongo
    async def get_pov_counts(self, story_id: str, user_id: str) -> List[dict]:
        cursor = await self.collection.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$unwind": "$scenes"},
            {"$group": {
                "_id": {
                    "chapter_number": "$chapter_number",
                    "chapter_id": "$chapter_id",
                    "pov": "$scenes.pov"
                },
                "count": {"$sum": 1},
                "estimated_word_count": {"$sum": "$scenes.word_count"}
            }},
            {"$sort": {"_id.chapter_number": 1}}
        ])
        return [doc async for doc in cursor]

    @retry_mongo
    async def get_pacing(self, story_id: str, user_id: str) -> List[dict]:
        cursor = await self.collection.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$project": {
                "_id": 0,
                "chapter_number": 1,
                "chapter_id": 1,
                "action_pct": "$pacing.action_pct",
                "dialogue_pct": "$pacing.dialogue_pct",
                "introspection_pct": "$pacing.introspection_pct",
                "exposition_pct": "$pacing.exposition_pct",
                "pace": "$pacing.pace",
                "tension": "$pacing.tension"
            }}
        ])
        return [doc async for doc in cursor]

    @retry_mongo
    async def get_structural_roles(self, story_id: str, user_id: str) -> List[dict]:
        cursor = await self.collection.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$project": {
                "_id": 0,
                "chapter_number": 1,
                "chapter_id": 1,
                "structural_role": 1
            }}
        ])
        return [doc async for doc in cursor]

    @retry_mongo
    async def get_theme_counts(self, story_id: str, user_id: str) -> List[dict]:
        cursor = await self.collection.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$unwind": "$themes"},
            {"$group": {
                "_id": "$themes.theme",
                "chapter_ids": {"$push": "$chapter_id"},
                "count": {"$sum": 1}
            }}
        ])
        return [doc async for doc in cursor]

    @retry_mongo
    async def get_emotional_beats(self, story_id: str, user_id: str) -> List[dict]:
        cursor = await self.collection.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$unwind": "$emotional_beats"},
            {"$group": {
                "_id": {"chapter_id": "$chapter_id", "chapter_number": "$chapter_number"},
                "strong": {"$sum": {"$cond": [{"$eq": ["$emotional_beats.effectiveness", "strong"]}, 1, 0]}},
                "moderate": {"$sum": {"$cond": [{"$eq": ["$emotional_beats.effectiveness", "moderate"]}, 1, 0]}},
                "weak": {"$sum": {"$cond": [{"$eq": ["$emotional_beats.effectiveness", "weak"]}, 1, 0]}},
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
