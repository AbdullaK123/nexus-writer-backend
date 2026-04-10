from typing import List
from pymongo.asynchronous.database import AsyncDatabase
from src.infrastructure.utils.retry import retry_mongo


class PlotExtractionRepo:

    def __init__(self, db: AsyncDatabase):
        self.collection = db.plot_extractions

    @retry_mongo
    async def get_unresolved_threads(self, story_id: str, user_id: str) -> List[dict]:
        cursor = await self.collection.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$unwind": "$threads"},
            {"$match": {"threads.status": {"$ne": "resolved"}, "threads.must_resolve": True}},
            {"$replaceRoot": {"newRoot": "$threads"}}
        ])
        return [doc async for doc in cursor]

    @retry_mongo
    async def get_raised_questions(self, story_id: str, user_id: str, min_importance: int = 5) -> List[dict]:
        cursor = await self.collection.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$unwind": "$questions"},
            {"$match": {"questions.status": {"$eq": "raised"}, "questions.importance": {"$gte": min_importance}}},
            {"$replaceRoot": {"newRoot": "$questions"}}
        ])
        return [doc async for doc in cursor]

    @retry_mongo
    async def get_answered_questions(self, story_id: str, user_id: str, min_importance: int = 5) -> List[dict]:
        cursor = await self.collection.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$unwind": "$questions"},
            {"$match": {"questions.status": {"$eq": "answered"}, "questions.importance": {"$gte": min_importance}}},
            {"$replaceRoot": {"newRoot": "$questions"}}
        ])
        return [doc async for doc in cursor]

    @retry_mongo
    async def get_must_pay_off_setups(self, story_id: str, user_id: str) -> List[dict]:
        cursor = await self.collection.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$unwind": "$setups"},
            {"$match": {"setups.must_pay_off": True}},
            {"$replaceRoot": {"newRoot": "$setups"}}
        ])
        return [doc async for doc in cursor]

    @retry_mongo
    async def get_all_payoffs(self, story_id: str, user_id: str) -> List[dict]:
        cursor = await self.collection.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$unwind": "$payoffs"},
            {"$replaceRoot": {"newRoot": "$payoffs"}}
        ])
        return [doc async for doc in cursor]

    @retry_mongo
    async def get_high_risk_contrivances(self, story_id: str, user_id: str) -> List[dict]:
        cursor = await self.collection.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$unwind": "$contrivance_risks"},
            {"$match": {"$or": [
                {"contrivance_risks.risk": {"$gte": 7}},
                {"contrivance_risks.has_prior_setup": False}
            ]}},
            {"$replaceRoot": {"newRoot": "$contrivance_risks"}}
        ])
        return [doc async for doc in cursor]

    @retry_mongo
    async def get_thread_timeline(self, story_id: str, user_id: str, thread_name: str) -> List[dict]:
        cursor = await self.collection.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$unwind": "$threads"},
            {"$match": {"threads.name": thread_name}},
            {"$project": {
                "_id": 0,
                "chapter_id": 1,
                "chapter_number": 1,
                "status": "$threads.status",
                "importance": "$threads.importance",
                "must_resolve": "$threads.must_resolve"
            }},
            {"$sort": {"chapter_number": 1}}
        ])
        return [doc async for doc in cursor]

    @retry_mongo
    async def get_thread_appearances(self, story_id: str, user_id: str) -> List[dict]:
        cursor = await self.collection.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$unwind": "$threads"},
            {"$project": {
                "_id": 0,
                "name": "$threads.name",
                "chapter_number": 1,
                "chapter_id": 1,
                "importance": "$threads.importance",
                "must_resolve": "$threads.must_resolve",
                "status": "$threads.status",
            }},
            {"$sort": {"chapter_number": 1}},
            {"$group": {
                "_id": "$name",
                "appearances": {
                    "$push": {
                        "chapter_number": "$chapter_number",
                        "chapter_id": "$chapter_id",
                        "importance": "$importance",
                        "must_resolve": "$must_resolve",
                        "status": "$status",
                    }
                }
            }}
        ])
        return [doc async for doc in cursor]

    @retry_mongo
    async def get_event_counts(self, story_id: str, user_id: str) -> List[dict]:
        cursor = await self.collection.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$unwind": "$events"},
            {"$group": {
                "_id": {"chapter_id": "$chapter_id", "chapter_number": "$chapter_number"},
                "event_count": {"$sum": 1}
            }},
            {"$sort": {"_id.chapter_number": 1}}
        ])
        return [doc async for doc in cursor]

    @retry_mongo
    async def get_setup_elements(self, story_id: str, user_id: str) -> List[dict]:
        cursor = await self.collection.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$unwind": "$setups"},
            {"$group": {
                "_id": "$setups.element",
                "emphasis": {"$max": "$setups.emphasis"},
                "must_pay_off": {"$max": "$setups.must_pay_off"},
            }}
        ])
        return [doc async for doc in cursor]

    @retry_mongo
    async def get_payoff_details(self, story_id: str, user_id: str) -> List[dict]:
        cursor = await self.collection.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$unwind": "$payoffs"},
            {"$project": {
                "_id": 0,
                "element": "$payoffs.element",
                "chapter_number": 1,
                "chapter_id": 1,
                "resolution": "$payoffs.resolution",
            }},
            {"$sort": {"chapter_number": 1}}
        ])
        return [doc async for doc in cursor]

    @retry_mongo
    async def get_plot_density(self, story_id: str, user_id: str) -> List[dict]:
        cursor = await self.collection.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$project": {
                "_id": 0,
                "chapter_number": 1,
                "chapter_id": 1,
                "event_count": {"$size": {"$ifNull": ["$events", []]}},
                "setup_count": {"$size": {"$ifNull": ["$setups", []]}},
                "payoff_count": {"$size": {"$ifNull": ["$payoffs", []]}},
                "question_count": {"$size": {"$ifNull": ["$questions", []]}},
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
