import asyncio
from src.service.exceptions import InternalError
from langchain.messages import HumanMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel
from src.shared.utils.logging_context import get_layer_logger, LAYER_SERVICE

log = get_layer_logger(LAYER_SERVICE)
from src.data.schemas.character import *
from src.service.ai.utils.ai import extract_text
from src.infrastructure.utils.retry import retry_llm
from src.data.repositories.mongo.character_extraction import CharacterExtractionRepo


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

    def __init__(self, repo: CharacterExtractionRepo, model: BaseChatModel):
        self.repo = repo
        self._model = model

    async def get_character_presence_map(
        self,
        story_id: str,
        user_id: str,
    ) -> CharacterAppearancesResponse:
        """Per-character list of chapters where they appear."""
        rows = await self.repo.get_presence_map(story_id, user_id)

        character_appearances = [
            CharacterAppearanceMap(
                character_name=row["_id"],
                appearances=[
                    CharacterAppearance(
                        chapter_number=appearance["chapter_number"],
                        chapter_id=appearance["chapter_id"]
                    )
                    for appearance in row["appearances"]
                ]
            )
            for row in rows
        ]

        return CharacterAppearancesResponse(maps=character_appearances)

    async def get_character_introduction_rate(
        self,
        story_id: str,
        user_id: str,
    ) -> CharacterIntroductionResponse:
        """Per-chapter count of newly introduced characters."""
        rows = await self.repo.get_introduction_rate(story_id, user_id)

        counts = [
            CharacterIntroductionCount(
                chapter_number=doc["_id"]["chapter_number"],
                chapter_id=doc["_id"]["chapter_id"],
                characters_introduced=doc["count"]
            )
            for doc in rows
        ]

        return CharacterIntroductionResponse(counts=counts)

    async def get_goal_evolution(
        self,
        story_id: str,
        user_id: str,
        character_name: str,
    ) -> CharacterGoalsResponse:
        """A single character's goals chapter by chapter."""
        rows = await self.repo.get_goal_evolution(story_id, user_id, character_name)

        chapter_goals = [ChapterGoals(**doc) for doc in rows]

        return CharacterGoalsResponse(
            character_name=character_name,
            goals=chapter_goals,
        )

    async def get_knowledge_asymmetry(
        self,
        story_id: str,
        user_id: str,
        character_name: str,
        chapter_number: int,
    ) -> CharacterKnowledgeMapResponse:
        """Cumulative knowledge for a character up to a given chapter."""
        rows = await self.repo.get_knowledge_asymmetry(story_id, user_id, character_name, chapter_number)

        maps = [CharacterKnowledgeMap(**doc) for doc in rows]

        return CharacterKnowledgeMapResponse(
            character_name=character_name,
            maps=maps,
        )

    async def get_cast_density(
        self,
        story_id: str,
        user_id: str,
    ) -> CharacterDensityResponse:
        """Per-chapter count of characters present."""
        rows = await self.repo.get_cast_density(story_id, user_id)

        counts = [ChapterCharacterDensity(**doc) for doc in rows]

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
                log.warning(f"Error generating cast management report: {str(result)}")
                raise InternalError("An error occurred while generating your report. Please try again later.")

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



