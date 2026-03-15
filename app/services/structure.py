from typing import Optional, Literal
from fastapi import Depends
from pymongo.asynchronous.database import AsyncDatabase
from app.core.mongodb import get_mongodb
from app.ai.models.structure import Scene
from app.schemas.structure import *


class StructureService:

    def __init__(self, mongodb: AsyncDatabase):
        self.mongodb = mongodb

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
            scene_filter.update({"scenes.type": str(scene_type)})

        if pov:
            scene_filter.update({"scenes.pov": pov})

        if location:
            scene_filter.update({"scenes.location": location})

        cursor = await self.mongodb.structure_extractions.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$unwind": "$scenes"},
            {"$match": scene_filter},
            {"$project": {
                "_id": 0,
                "chapter_id": 1,
                "chapter_number": 1,
                "scene": "$scenes"
            }},
            {"$sort": {"chapter_number": 1}}
        ])

        scenes = [
            SceneWithContext.from_scene(
                chapter_number=doc["chapter_number"],
                chapter_id=doc["chapter_id"],
                scene=Scene.model_validate(doc["scene"])
            )
            async for doc in cursor
        ]
        return SceneIndexResponse(scenes=scenes)

    async def get_weak_scenes(
        self,
        story_id: str,
        user_id: str,
    ) -> WeakScenesResponse:
        """Scenes missing goal, conflict, or outcome. Grouped by chapter."""

        cursor = await self.mongodb.structure_extractions.aggregate([
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

        chapter_scenes = [
            ChapterScenes(
                chapter_number=doc["_id"]["chapter_number"],
                chapter_id=doc["_id"]["chapter_id"],
                scenes=[
                    Scene(**scene)
                    for scene in doc["scenes"]
                ]
            )
            async for doc in cursor
        ]

        return WeakScenesResponse(weak_scenes=chapter_scenes)



    async def get_scene_type_distribution(
        self,
        story_id: str,
        user_id: str,
    ) -> SceneTypeDistributionResponse:
        """Per-chapter scene type counts and percentages."""

        cursor = await self.mongodb.structure_extractions.aggregate([
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

        rows = [doc async for doc in cursor]

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
        cursor = await self.mongodb.structure_extractions.aggregate([
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

        rows = [doc async for doc in cursor]

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

        cursor = await self.mongodb.structure_extractions.aggregate([
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

        chapter_distributions = [
            ChapterPacingDistribution(**doc)
            async for doc in cursor
        ]

        return PacingCurveResponse(chapter_distributions=chapter_distributions)


    async def get_structural_arc(
        self,
        story_id: str,
        user_id: str,
    ) -> StructuralArcResponse:
        """Ordered chapter roles showing the story's structural shape."""
        
        cursor = await self.mongodb.structure_extractions.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$project": {
                "_id": 0,
                "chapter_number": 1,
                "chapter_id": 1,
                "structural_role": 1
            }}
        ])

        roles = [
            ChapterRole(**doc)
            async for doc in cursor
        ]

        return StructuralArcResponse(roles=roles)

    async def get_theme_tracker(
        self,
        story_id: str,
        user_id: str,
    ) -> ThemeDistributionResponse:
        """Per-theme appearance counts, percentages, and chapter IDs."""

        cursor = await self.mongodb.structure_extractions.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$unwind": "$themes"},
            {"$group": {
                "_id": "$themes.theme",
                "chapter_ids": {"$push": "$chapter_id"},
                "count": {"$sum": 1}
            }}
        ])

        rows = [doc async for doc in cursor]

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
        
        cursor = await self.mongodb.structure_extractions.aggregate([
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

        chapter_distributions = [
            ChapterEmotionalBeats(
                chapter_number=doc["_id"]["chapter_number"],
                chapter_id=doc["_id"]["chapter_id"],
                strong=doc["strong"],
                moderate=doc["moderate"],
                weak=doc["weak"]
            )
            async for doc in cursor
        ]
        return EmotionalBeatsResponse(chapter_distributions=chapter_distributions)




async def get_structure_service(
    mongodb: AsyncDatabase = Depends(get_mongodb)
) -> StructureService:
    return StructureService(mongodb=mongodb)