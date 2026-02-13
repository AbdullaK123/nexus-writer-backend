from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import pymongo
import asyncio

class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

    @classmethod
    async def connect(cls, url: str):
        cls.client = AsyncIOMotorClient(url)
        cls.db = cls.client.get_database("nexus_extractions")
        
        # Create indexes for all collections
        await cls._create_indexes()

    @classmethod
    async def _create_indexes(cls):
        """Create all necessary indexes for MongoDB collections"""
        if cls.db is None:
            return
        
        # Create indexes in parallel
        await asyncio.gather(
            # chapter_edits indexes
            cls.db.chapter_edits.create_index("chapter_id", unique=True),
            cls.db.chapter_edits.create_index("story_id"),
            cls.db.chapter_edits.create_index([("story_id", pymongo.ASCENDING), ("chapter_number", pymongo.ASCENDING)]),
            
            # character_extractions indexes
            cls.db.character_extractions.create_index("chapter_id", unique=True),
            cls.db.character_extractions.create_index("story_id"),
            cls.db.character_extractions.create_index([("story_id", pymongo.ASCENDING), ("chapter_number", pymongo.ASCENDING)]),
            
            # plot_extractions indexes
            cls.db.plot_extractions.create_index("chapter_id", unique=True),
            cls.db.plot_extractions.create_index("story_id"),
            cls.db.plot_extractions.create_index([("story_id", pymongo.ASCENDING), ("chapter_number", pymongo.ASCENDING)]),
            
            # world_extractions indexes
            cls.db.world_extractions.create_index("chapter_id", unique=True),
            cls.db.world_extractions.create_index("story_id"),
            cls.db.world_extractions.create_index([("story_id", pymongo.ASCENDING), ("chapter_number", pymongo.ASCENDING)]),
            
            # structure_extractions indexes
            cls.db.structure_extractions.create_index("chapter_id", unique=True),
            cls.db.structure_extractions.create_index("story_id"),
            cls.db.structure_extractions.create_index([("story_id", pymongo.ASCENDING), ("chapter_number", pymongo.ASCENDING)]),
            
            # chapter_contexts indexes
            cls.db.chapter_contexts.create_index("chapter_id", unique=True),
            cls.db.chapter_contexts.create_index("story_id"),
            cls.db.chapter_contexts.create_index([("story_id", pymongo.ASCENDING), ("chapter_number", pymongo.ASCENDING)]),
        )
    
    @classmethod
    async def close(cls):
        if cls.client:
            cls.client.close()


def get_mongodb() -> AsyncIOMotorDatabase:
    if MongoDB.db is None:
        raise Exception("MongoDB client is not connected. Call MongoDB.connect() first.")
    return MongoDB.db