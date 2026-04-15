from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase
from typing import Optional
import pymongo
import asyncio

from src.infrastructure.utils.retry import retry_mongo


class MongoDB:
    client: Optional[AsyncMongoClient] = None
    db: Optional[AsyncDatabase] = None

    @classmethod
    async def connect(cls, url: str, database_name: str = "nexus_extractions"):
        cls.client = AsyncMongoClient(url)
        cls.db = cls.client.get_database(database_name)

        # Create indexes for all collections
        await cls._create_indexes()

    @classmethod
    @retry_mongo
    async def _create_indexes(cls):
        """Create all necessary indexes for MongoDB collections"""
        if cls.db is None:
            return

        # Create indexes in parallel
        await asyncio.gather(
            # chapter_edits indexes
            cls.db.chapter_edits.create_index("chapter_id", unique=True),
            cls.db.chapter_edits.create_index("story_id"),
            cls.db.chapter_edits.create_index(
                [("story_id", pymongo.ASCENDING), ("chapter_number", pymongo.ASCENDING)]
            ),
            # character_extractions indexes
            cls.db.character_extractions.create_index("chapter_id", unique=True),
            cls.db.character_extractions.create_index("story_id"),
            cls.db.character_extractions.create_index(
                [("story_id", pymongo.ASCENDING), ("chapter_number", pymongo.ASCENDING)]
            ),
            # plot_extractions indexes
            cls.db.plot_extractions.create_index("chapter_id", unique=True),
            cls.db.plot_extractions.create_index("story_id"),
            cls.db.plot_extractions.create_index(
                [("story_id", pymongo.ASCENDING), ("chapter_number", pymongo.ASCENDING)]
            ),
            # world_extractions indexes
            cls.db.world_extractions.create_index("chapter_id", unique=True),
            cls.db.world_extractions.create_index("story_id"),
            cls.db.world_extractions.create_index(
                [("story_id", pymongo.ASCENDING), ("chapter_number", pymongo.ASCENDING)]
            ),
            # structure_extractions indexes
            cls.db.structure_extractions.create_index("chapter_id", unique=True),
            cls.db.structure_extractions.create_index("story_id"),
            cls.db.structure_extractions.create_index(
                [("story_id", pymongo.ASCENDING), ("chapter_number", pymongo.ASCENDING)]
            ),
            # chapter_contexts indexes
            cls.db.chapter_contexts.create_index("chapter_id", unique=True),
            cls.db.chapter_contexts.create_index("story_id"),
            cls.db.chapter_contexts.create_index(
                [("story_id", pymongo.ASCENDING), ("chapter_number", pymongo.ASCENDING)]
            ),
        )

    @classmethod
    async def close(cls):
        if cls.client:
            await cls.client.close()


def get_mongodb() -> AsyncDatabase:
    if MongoDB.db is None:
        raise Exception(
            "MongoDB client is not connected. Call MongoDB.connect() first."
        )
    return MongoDB.db
