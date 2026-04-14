import asyncio
from typing import Optional, Literal
from src.service.exceptions import InternalError
from langchain.messages import HumanMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel
from src.data.models.ai.structure import Scene
from src.service.ai.prompts.structure import DEVELOPMENTAL_REPORT_SYSTEM_PROMPT
from src.data.schemas.structure import *
from src.service.ai.utils.ai import extract_text
from src.infrastructure.utils.retry import retry_llm
from src.data.repositories.mongo.structure_extraction import StructureExtractionRepo
from loguru import logger


class StructureService:

    def __init__(self, repo: StructureExtractionRepo, model: BaseChatModel):
        self.repo = repo
        self._model = model

    async def get_scene_index(
        self,
        story_id: str,
        user_id: str,
        scene_type: Optional[Literal["action", "dialogue", "introspection", "exposition", "transition"]] = None,
        pov: Optional[str] = None,
        location: Optional[str] = None,
    ) -> SceneIndexResponse:
        """Flat list of every scene across all chapters. Filterable by type, POV, and location."""
        
        scene_filter = {}
        if scene_type:
            scene_filter["scenes.type"] = str(scene_type)
        if pov:
            scene_filter["scenes.pov"] = pov
        if location:
            scene_filter["scenes.location"] = location

        rows = await self.repo.get_scenes(story_id, user_id, scene_filter or None)

        scenes = [
            SceneWithContext.from_scene(
                chapter_number=doc["chapter_number"],
                chapter_id=doc["chapter_id"],
                scene=Scene.model_validate(doc["scene"])
            )
            for doc in rows
        ]
        return SceneIndexResponse(scenes=scenes)

    async def get_weak_scenes(
        self,
        story_id: str,
        user_id: str,
    ) -> WeakScenesResponse:
        """Scenes missing goal, conflict, or outcome. Grouped by chapter."""
        rows = await self.repo.get_weak_scenes(story_id, user_id)

        chapter_scenes = [
            ChapterScenes(
                chapter_number=doc["_id"]["chapter_number"],
                chapter_id=doc["_id"]["chapter_id"],
                scenes=[Scene(**scene) for scene in doc["scenes"]]
            )
            for doc in rows
        ]

        return WeakScenesResponse(weak_scenes=chapter_scenes)

    async def get_scene_type_distribution(
        self,
        story_id: str,
        user_id: str,
    ) -> SceneTypeDistributionResponse:
        """Per-chapter scene type counts and percentages."""
        rows = await self.repo.get_scene_type_counts(story_id, user_id)

        # Build per-chapter totals
        chapter_totals: dict[str, int] = {}
        for row in rows:
            ch_id = row["_id"]["chapter_id"]
            chapter_totals[ch_id] = chapter_totals.get(ch_id, 0) + row["count"]

        # Group rows by chapter
        chapter_rows: dict[str, list] = {}
        for row in rows:
            ch_id = row["_id"]["chapter_id"]
            chapter_rows.setdefault(ch_id, []).append(row)

        chapter_distributions = [
            ChapterSceneDistribution(
                chapter_number=group[0]["_id"]["chapter_number"],
                chapter_id=ch_id,
                distributions=[
                    SceneDistribution(
                        type=row["_id"]["type"],
                        scene_count=row["count"],
                        pct=round(row["count"] / chapter_totals[ch_id], 2)
                    )
                    for row in group
                ]
            )
            for ch_id, group in chapter_rows.items()
        ]

        return SceneTypeDistributionResponse(chapter_distributions=chapter_distributions)

    async def get_pov_balance(
        self,
        story_id: str,
        user_id: str,
    ) -> POVBalanceResponse:
        """Per-chapter POV distribution by scene count and estimated word count."""
        rows = await self.repo.get_pov_counts(story_id, user_id)

        # Build per-chapter totals
        chapter_totals: dict[str, int] = {}
        for row in rows:
            ch_id = row["_id"]["chapter_id"]
            chapter_totals[ch_id] = chapter_totals.get(ch_id, 0) + row["count"]

        # Group rows by chapter
        chapter_rows: dict[str, list] = {}
        for row in rows:
            ch_id = row["_id"]["chapter_id"]
            chapter_rows.setdefault(ch_id, []).append(row)

        chapter_distributions = [
            ChapterPOVBalance(
                chapter_number=group[0]["_id"]["chapter_number"],
                chapter_id=ch_id,
                distributions=[
                    POVDistribution(
                        pov=row["_id"]["pov"],
                        scene_count=row["count"],
                        estimated_word_count=row["estimated_word_count"],
                        pct=round(row["count"] / chapter_totals[ch_id], 2)
                    )
                    for row in group
                ]
            )
            for ch_id, group in chapter_rows.items()
        ]

        return POVBalanceResponse(chapter_distributions=chapter_distributions)

    async def get_pacing_curve(
        self,
        story_id: str,
        user_id: str,
    ) -> PacingCurveResponse:
        """Per-chapter pacing data ordered by chapter number."""
        rows = await self.repo.get_pacing(story_id, user_id)
        chapter_distributions = [ChapterPacingDistribution(**doc) for doc in rows]
        return PacingCurveResponse(chapter_distributions=chapter_distributions)

    async def get_structural_arc(
        self,
        story_id: str,
        user_id: str,
    ) -> StructuralArcResponse:
        """Ordered chapter roles showing the story's structural shape."""
        rows = await self.repo.get_structural_roles(story_id, user_id)
        roles = [ChapterRole(**doc) for doc in rows]
        return StructuralArcResponse(roles=roles)

    async def get_theme_tracker(
        self,
        story_id: str,
        user_id: str,
    ) -> ThemeDistributionResponse:
        """Per-theme appearance counts, percentages, and chapter IDs."""
        rows = await self.repo.get_theme_counts(story_id, user_id)

        total = sum(doc["count"] for doc in rows)

        theme_distributions = [
            ThemeDistribution(
                chapter_ids=row["chapter_ids"],
                theme=row["_id"],
                count=row["count"],
                perc=round(100*row["count"] / total, 2)
            )
            for row in rows
        ]

        return ThemeDistributionResponse(theme_distributions=theme_distributions)

    async def get_emotional_beat_report(
        self,
        story_id: str,
        user_id: str,
    ) -> EmotionalBeatsResponse:
        """Per-chapter strong/moderate/weak emotional beat counts."""
        rows = await self.repo.get_emotional_beats(story_id, user_id)

        chapter_distributions = [
            ChapterEmotionalBeats(
                chapter_number=doc["_id"]["chapter_number"],
                chapter_id=doc["_id"]["chapter_id"],
                strong=doc["strong"],
                moderate=doc["moderate"],
                weak=doc["weak"]
            )
            for doc in rows
        ]
        return EmotionalBeatsResponse(chapter_distributions=chapter_distributions)

    def _build_developmental_report_prompt(
        self,
        pacing: PacingCurveResponse,
        arc: StructuralArcResponse,
        weak: WeakScenesResponse,
        emotional: EmotionalBeatsResponse,
    ) -> str:

        pacing_curve = "\n".join(
            f"  Ch {p.chapter_number}: pace={p.pace}, tension={p.tension}, "
            f"action={p.action_pct}% dialogue={p.dialogue_pct}% "
            f"introspection={p.introspection_pct}% exposition={p.exposition_pct}%"
            for p in pacing.chapter_distributions  # type: ignore
        ) or "  No pacing data."

        structural_arc = "\n".join(
            f"  Ch {r.chapter_number}: {r.structural_role}"
            for r in arc.roles  # type: ignore
        ) or "  No structural roles."

        weak_scenes = "\n".join(
            f"  Ch {ch.chapter_number}: {len(ch.scenes)} weak scene(s) — "  # type: ignore[arg-type]
            + ", ".join(
                f"{s.type} (goal={'✓' if s.goal else '✗'} conflict={'✓' if s.conflict else '✗'} outcome={'✓' if s.outcome else '✗'})"
                for s in ch.scenes  # type: ignore
            )
            for ch in weak.weak_scenes  # type: ignore
        ) or "  None."

        emotional_beats = "\n".join(
            f"  Ch {e.chapter_number}: strong={e.strong} moderate={e.moderate} weak={e.weak}"
            for e in emotional.chapter_distributions  # type: ignore
        ) or "  No emotional beat data."

        return f"""
PACING CURVE:
{pacing_curve}

STRUCTURAL ARC:
{structural_arc}

WEAK SCENES (missing goal, conflict, or outcome):
{weak_scenes}

EMOTIONAL BEAT EFFECTIVENESS:
{emotional_beats}
"""

    @retry_llm
    async def get_developmental_report(
        self,
        story_id: str,
        user_id: str,
    ) -> DevelopmentalReportResponse:
        """AI-generated developmental editor report synthesizing structural metrics."""

        results = await asyncio.gather(
            self.get_pacing_curve(story_id, user_id),
            self.get_structural_arc(story_id, user_id),
            self.get_weak_scenes(story_id, user_id),
            self.get_emotional_beat_report(story_id, user_id),
            return_exceptions=True,
        )

        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Error generating developmental report: {str(result)}")
                raise InternalError("An error occurred while generating your report. Please try again later.")

        pacing, arc, weak, emotional = results

        response = await self._model.ainvoke([
            SystemMessage(content=DEVELOPMENTAL_REPORT_SYSTEM_PROMPT),
            HumanMessage(content=self._build_developmental_report_prompt(
                pacing,   # type: ignore
                arc,      # type: ignore
                weak,     # type: ignore
                emotional,  # type: ignore
            )),
        ])

        return DevelopmentalReportResponse(
            story_id=story_id,
            report=extract_text(response),
        )



