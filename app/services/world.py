import asyncio
from typing import Any, Optional
from fastapi import Depends, HTTPException, status
from langchain.messages import HumanMessage, SystemMessage
from pymongo.asynchronous.database import AsyncDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.mongodb import get_mongodb
from app.config.settings import app_config
from app.ai.prompts.world import WORLD_CONSISTENCY_REPORT_SYSTEM_PROMPT
from app.schemas.world import *
from app.utils.ai import extract_text
from app.utils.retry import retry_llm, retry_mongo
from loguru import logger


class WorldConsistencyService:

    def __init__(self, mongodb: AsyncDatabase):
        self.mongodb = mongodb
        self._model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            temperature=app_config.ai_temperature,
            max_tokens=app_config.ai_maxtokens,
            timeout=app_config.ai_sdk_timeout,
            max_retries=app_config.ai_sdk_retries,
        )

    @retry_mongo
    async def get_contradictions(
        self,
        story_id: str,
        user_id: str,
    ) -> ContradictionResponse:
        """Entity+attribute pairs with conflicting values across chapters."""
        
        cursor = await self.mongodb.world_extractions.aggregate([
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

        rows = [row async for row in cursor]

        rows_as_triplets = [
            (row["_id"]["entity"], row["_id"]["attribute"], row["facts"])
            for row in rows
        ]

        contradictions = [
            Contradiction(
                entity=row[0],
                attribute=row[1],
                occurrences=[
                    ContradictingFact(
                        chapter_number=occurrence["chapter_number"],
                        chapter_id=occurrence["chapter_id"],
                        value=occurrence["value"]
                    )
                    for occurrence in row[2]
                ]
            )
            for row in rows_as_triplets
        ]

        return ContradictionResponse(contradictions=contradictions)

    @retry_mongo
    async def get_entity_registry(
        self,
        story_id: str,
        user_id: str,
        entities: Optional[List[str]] = [],
    ) -> List[EntityFactResponse]:
        """Latest known attributes for each entity. Optionally filter to a single entity."""
        
        filter: dict[str, Any] = {"story_id": story_id, "user_id": user_id}

        if entities and len(entities) > 0:
            filter.update({"facts.entity": { "$in": entities}})

        cursor = await self.mongodb.world_extractions.aggregate([
            {"$match": filter},
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
            }}}
        ])

        rows = [row async for row in cursor]

        rows_as_tuples = [
            (row["_id"], row["facts"])
            for row in rows
        ]

        entity_facts = [
            EntityFactResponse(
                entity=row_tuple[0],
                facts=[
                    EntityFact(
                        attribute=fact["attribute"],
                        value=fact["value"]
                    )
                    for fact in row_tuple[1]
                ]
            )
            for row_tuple in rows_as_tuples
        ]

        return entity_facts

    @retry_mongo
    async def get_entity_timeline(
        self,
        story_id: str,
        user_id: str,
        entity: str,
    ) -> EntityTimelineResponse:
        """All attribute changes for a given entity in chapter order."""
        
        cursor = await self.mongodb.world_extractions.aggregate([
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

        rows = [row async for row in cursor]

        rows_as_tuples = [
            (row["_id"]["chapter_number"], row["_id"]["chapter_id"], row["facts"])
            for row in rows
        ]

        chapter_facts = [
            ChapterEntityFacts(
                chapter_number=row_tuple[0],
                chapter_id=row_tuple[1],
                facts=[
                    EntityFact(
                        attribute=fact["attribute"],
                        value=fact["value"]
                    )
                    for fact in row_tuple[2]
                ]
            )
            for row_tuple in rows_as_tuples
        ]

        return EntityTimelineResponse(chapter_facts=chapter_facts)


    @retry_mongo
    async def get_fact_density(
        self,
        story_id: str,
        user_id: str,
    ) -> StoryFactCountsResponse:
        """Fact count per chapter. Spots worldbuilding-heavy and worldbuilding-thin chapters."""
        
        cursor = await self.mongodb.world_extractions.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$unwind": "$facts"},
            {"$group": {
                "_id": {"chapter_number": "$chapter_number", "chapter_id": "$chapter_id"},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id.chapter_number": 1}}
        ])

        counts = [
            ChapterFactCount(
                chapter_number=doc["_id"]["chapter_number"],
                chapter_id=doc["_id"]["chapter_id"],
                count=doc["count"]
            )
            async for doc in cursor
        ]

        return StoryFactCountsResponse(counts=counts)

    def _build_consistency_prompt(
        self,
        contradictions: ContradictionResponse,
        fact_density: StoryFactCountsResponse,
    ) -> str:

        contradiction_lines = "\n".join(
            f"  - {c.entity}.{c.attribute}: "
            + ", ".join(
                f"Ch.{o.chapter_number}='{o.value}'" for o in c.occurrences  # type: ignore
            )
            for c in contradictions.contradictions  # type: ignore
        ) or "  None."

        density_lines = "\n".join(
            f"  Chapter {d.chapter_number}: {d.count} facts"
            for d in fact_density.counts  # type: ignore
        ) or "  No data."

        return f"""
CONTRADICTIONS:
{contradiction_lines}

FACT DENSITY BY CHAPTER:
{density_lines}
"""

    @retry_llm
    async def get_consistency_report(
        self,
        story_id: str,
        user_id: str,
    ) -> WorldConsistencyReport:
        """AI-generated continuity report triaging contradictions and worldbuilding gaps."""

        results = await asyncio.gather(
            self.get_contradictions(story_id, user_id),
            self.get_fact_density(story_id, user_id),
            return_exceptions=True,
        )

        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Error generating consistency report: {str(result)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="An error occurred while generating your report. Please try again later.",
                )

        contradictions, fact_density = results

        response = await self._model.ainvoke([
            SystemMessage(content=WORLD_CONSISTENCY_REPORT_SYSTEM_PROMPT),
            HumanMessage(content=self._build_consistency_prompt(
                contradictions,  # type: ignore
                fact_density,  # type: ignore
            )),
        ])

        return WorldConsistencyReport(
            story_id=story_id,
            report=extract_text(response),
        )


async def get_world_consistency_service(
    mongodb: AsyncDatabase = Depends(get_mongodb)
) -> WorldConsistencyService:
    return WorldConsistencyService(mongodb=mongodb)