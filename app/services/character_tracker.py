import asyncio
from typing import Optional
from fastapi import Depends, HTTPException, status
from pymongo.asynchronous.database import AsyncDatabase
from langchain.messages import HumanMessage, SystemMessage
from loguru import logger
from app.core.mongodb import get_mongodb
from app.config.settings import app_config
from app.ai.utils.model_factory import create_chat_model
from app.schemas.character import *
from app.utils.ai import extract_text
from app.utils.retry import retry_llm, retry_mongo


CAST_MANAGEMENT_REPORT_SYSTEM_PROMPT = """You are a story editor evaluating how well an author manages their cast of characters across a manuscript.

You will receive three datasets extracted from a manuscript:
1. CHARACTER PRESENCE MAP — which chapters each character appears in
2. INTRODUCTION RATE — how many new characters are introduced per chapter
3. CAST DENSITY — how many characters are present in each chapter

Your job is to assess whether the cast is well-balanced and well-managed. Do NOT just restate the data. Interpret it.

FOR CHARACTER PRESENCE:
- Flag characters who appear once or twice and then vanish — they may be unnecessary or forgotten.
- Flag characters with long gaps between appearances — the reader may forget them.
- Note which characters are consistently present (the core cast) and whether they crowd out others.
- Look for characters who appear in clusters — this may indicate they're tied to a subplot that itself has pacing issues.

FOR INTRODUCTION RATE:
- Flag chapters that introduce 3+ new characters — this overwhelms the reader.
- Flag runs of chapters that each introduce new characters — the reader can't keep up.
- Note whether introductions are front-loaded (common and often fine) or scattered throughout (harder to manage).
- Early chapters can sustain more introductions; late introductions need strong justification.

FOR CAST DENSITY:
- Flag chapters with very high character counts — scenes with 5+ characters are hard to manage and often leave some characters as wallpaper.
- Flag chapters where density spikes suddenly — the reader has to track too many people at once.
- Note the overall trend: does density grow steadily, or does it spike and drop?

FORMAT:
Write 3-6 paragraphs of direct, actionable feedback. Lead with the most damaging issue — the thing most likely to confuse or lose readers. Reference specific chapter numbers throughout. For each problem, suggest a concrete fix: not "reduce the cast" but "consider cutting the guard captain from Chapter 7 — they serve the same function as the lieutenant introduced in Chapter 3."

End with what's working — which characters are well-managed, which introductions land effectively, which sections have good cast balance. Writers need to know what to protect during revisions."""


class CharacterTrackerService:

    def __init__(self, mongodb: AsyncDatabase):
        self.mongodb = mongodb
        self._model = create_chat_model(app_config.ai_lite_model)

    @retry_mongo
    async def get_character_presence_map(
        self,
        story_id: str,
        user_id: str,
    ) -> CharacterAppearancesResponse:
        """Per-character list of chapters where they appear."""
        
        cursor = await self.mongodb.character_extractions.aggregate([
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

        rows = [doc async for doc in cursor]

        rows_as_tuples = [
            (row["_id"], row["appearances"])
            for row in rows
        ]

        character_appearances = [
            CharacterAppearanceMap(
                character_name=row[0],
                appearances=[
                    CharacterAppearance(
                        chapter_number=appearance["chapter_number"],
                        chapter_id=appearance["chapter_id"]
                    )
                    for appearance in row[1]
                ]
            )
            for row in rows_as_tuples
        ]

        return CharacterAppearancesResponse(maps=character_appearances)

    @retry_mongo
    async def get_character_introduction_rate(
        self,
        story_id: str,
        user_id: str,
    ) -> CharacterIntroductionResponse:
        """Per-chapter count of newly introduced characters."""

        cursor = await self.mongodb.character_extractions.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$unwind": "$characters"},
            {"$match": {"characters.is_new": True}},
            {"$group": {
                "_id": {"chapter_id": "$chapter_id", "chapter_number": "$chapter_number"},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id.chapter_number": 1}}
        ])

        counts = [
            CharacterIntroductionCount(
                chapter_number=doc["_id"]["chapter_number"],
                chapter_id=doc["_id"]["chapter_id"],
                characters_introduced=doc["count"]
            )
            async for doc in cursor
        ]

        return CharacterIntroductionResponse(counts=counts)

    @retry_mongo
    async def get_goal_evolution(
        self,
        story_id: str,
        user_id: str,
        character_name: str,
    ) -> CharacterGoalsResponse:
        """A single character's goals chapter by chapter."""
        cursor = await self.mongodb.character_extractions.aggregate([
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

        chapter_goals = [
            ChapterGoals(**doc)
            async for doc in cursor
        ]

        return CharacterGoalsResponse(
            character_name=character_name,
            goals=chapter_goals,
        )

    @retry_mongo
    async def get_knowledge_asymmetry(
        self,
        story_id: str,
        user_id: str,
        character_name: str,
        chapter_number: int,
    ) -> CharacterKnowledgeMapResponse:
        """Cumulative knowledge for a character up to a given chapter."""

        cursor = await self.mongodb.character_extractions.aggregate([
            {"$match": {
                "story_id": story_id,
                "user_id": user_id,
                "chapter_number": {"$lte": chapter_number},
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

        maps = [
            CharacterKnowledgeMap(**doc)
            async for doc in cursor
        ]

        return CharacterKnowledgeMapResponse(
            character_name=character_name,
            maps=maps,
        )

    @retry_mongo
    async def get_cast_density(
        self,
        story_id: str,
        user_id: str,
    ) -> CharacterDensityResponse:
        """Per-chapter count of characters present."""

        cursor = await self.mongodb.character_extractions.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$project": {
                "_id": 0,
                "chapter_id": 1,
                "chapter_number": 1,
                "characters_present": {"$size": {"$ifNull": ["$characters", []]}},
            }},
            {"$sort": {"chapter_number": 1}}
        ])

        counts = [
            ChapterCharacterDensity(**doc)
            async for doc in cursor
        ]

        return CharacterDensityResponse(counts=counts)

    @retry_llm
    async def get_cast_management_report(
        self,
        story_id: str,
        user_id: str,
    ) -> CastManagementReportResponse:
        """AI-generated report on cast balance, introduction pacing, and presence gaps."""

        results = await asyncio.gather(
            self.get_character_presence_map(story_id, user_id),
            self.get_character_introduction_rate(story_id, user_id),
            self.get_cast_density(story_id, user_id),
            return_exceptions=True
        )

        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Error generating cast management report: {str(result)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="An error occurred while generating your report. Please try again later."
                )

        presence, introductions, density = results

        response = await self._model.ainvoke([
            SystemMessage(content=CAST_MANAGEMENT_REPORT_SYSTEM_PROMPT),
            HumanMessage(content=self._build_cast_management_prompt(
                presence, #type: ignore
                introductions, #type: ignore
                density, #type: ignore
            ))
        ])

        return CastManagementReportResponse(
            story_id=story_id,
            report=extract_text(response.content)
        )

    def _build_cast_management_prompt(
        self,
        presence: CharacterAppearancesResponse,
        introductions: CharacterIntroductionResponse,
        density: CharacterDensityResponse,
    ) -> str:

        presence_lines = "\n".join(
            f"  - {m.character_name}: chapters {', '.join(str(a.chapter_number) for a in m.appearances)}" #type: ignore
            for m in presence.maps #type: ignore
        ) or "  None."

        introduction_lines = "\n".join(
            f"  - Chapter {c.chapter_number}: {c.characters_introduced} new characters"
            for c in introductions.counts #type: ignore
        ) or "  None."

        density_lines = "\n".join(
            f"  - Chapter {c.chapter_number}: {c.characters_present} characters"
            for c in density.counts #type: ignore
        ) or "  None."

        return f"""
CHARACTER PRESENCE MAP:
{presence_lines}

INTRODUCTION RATE:
{introduction_lines}

CAST DENSITY:
{density_lines}
"""


async def get_character_tracker_service(
    mongodb: AsyncDatabase = Depends(get_mongodb)
) -> CharacterTrackerService:
    return CharacterTrackerService(mongodb=mongodb)