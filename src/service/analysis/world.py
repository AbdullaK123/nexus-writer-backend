import asyncio
from typing import Any, List, Optional
from fastapi import Depends
from src.service.exceptions import InternalError
from langchain.messages import HumanMessage, SystemMessage
from src.infrastructure.db.mongodb import get_mongodb
from src.infrastructure.config import config
from src.service.ai.utils.model_factory import create_chat_model
from src.service.ai.prompts.world import WORLD_CONSISTENCY_REPORT_SYSTEM_PROMPT
from src.data.schemas.world import *
from src.service.ai.utils.ai import extract_text
from src.infrastructure.utils.retry import retry_llm
from src.data.repositories.mongo.world_extraction import WorldExtractionRepo
from loguru import logger


class WorldConsistencyService:

    def __init__(self, repo: WorldExtractionRepo):
        self.repo = repo
        self._model = create_chat_model(config.ai.lite_model)

    async def get_contradictions(
        self,
        story_id: str,
        user_id: str,
    ) -> ContradictionResponse:
        """Entity+attribute pairs with conflicting values across chapters."""
        rows = await self.repo.get_contradictions(story_id, user_id)

        contradictions = [
            Contradiction(
                entity=row["_id"]["entity"],
                attribute=row["_id"]["attribute"],
                occurrences=[
                    ContradictingFact(
                        chapter_number=occurrence["chapter_number"],
                        chapter_id=occurrence["chapter_id"],
                        value=occurrence["value"]
                    )
                    for occurrence in row["facts"]
                ]
            )
            for row in rows
        ]

        return ContradictionResponse(contradictions=contradictions)

    async def get_entity_registry(
        self,
        story_id: str,
        user_id: str,
        entities: Optional[List[str]] = [],
    ) -> List[EntityFactResponse]:
        """Latest known attributes for each entity. Optionally filter to specific entities."""
        rows = await self.repo.get_entity_registry(story_id, user_id, entities if entities else None)

        entity_facts = [
            EntityFactResponse(
                entity=row["_id"],
                facts=[
                    EntityFact(
                        attribute=fact["attribute"],
                        value=fact["value"]
                    )
                    for fact in row["facts"]
                ]
            )
            for row in rows
        ]

        return entity_facts

    async def get_entity_timeline(
        self,
        story_id: str,
        user_id: str,
        entity: str,
    ) -> EntityTimelineResponse:
        """All attribute changes for a given entity in chapter order."""
        rows = await self.repo.get_entity_timeline(story_id, user_id, entity)

        chapter_facts = [
            ChapterEntityFacts(
                chapter_number=row["_id"]["chapter_number"],
                chapter_id=row["_id"]["chapter_id"],
                facts=[
                    EntityFact(
                        attribute=fact["attribute"],
                        value=fact["value"]
                    )
                    for fact in row["facts"]
                ]
            )
            for row in rows
        ]

        return EntityTimelineResponse(chapter_facts=chapter_facts)

    async def get_fact_density(
        self,
        story_id: str,
        user_id: str,
    ) -> StoryFactCountsResponse:
        """Fact count per chapter. Spots worldbuilding-heavy and worldbuilding-thin chapters."""
        rows = await self.repo.get_fact_density(story_id, user_id)

        counts = [
            ChapterFactCount(
                chapter_number=doc["_id"]["chapter_number"],
                chapter_id=doc["_id"]["chapter_id"],
                count=doc["count"]
            )
            for doc in rows
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
                raise InternalError("An error occurred while generating your report. Please try again later.")

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
    mongodb=Depends(get_mongodb)
) -> WorldConsistencyService:
    return WorldConsistencyService(repo=WorldExtractionRepo(mongodb))
