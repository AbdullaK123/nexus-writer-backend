import asyncio
from typing import Optional
from fastapi import Depends, HTTPException, status
from pymongo.asynchronous.database import AsyncDatabase
from langchain.messages import HumanMessage, SystemMessage
from loguru import logger
from app.core.mongodb import get_mongodb
from app.config.settings import app_config
from app.ai.utils.model_factory import create_chat_model
from app.schemas.plot import *
from app.utils.ai import extract_text
from app.utils.retry import retry_llm, retry_mongo


PLOT_RHYTHM_REPORT_SYSTEM_PROMPT = """You are a story structure analyst evaluating a manuscript's plot rhythm and thread management.

You will receive three datasets extracted from a manuscript:
1. DORMANT THREADS — plot threads that disappeared for multiple consecutive chapters before reappearing
2. EVENT DENSITY — how many plot events each chapter contains
3. SETUP-PAYOFF MAP — every narrative setup paired with its payoffs (or lack thereof)

Your job is to assess how well the author juggles plot elements across the story. Do NOT just restate the data. Interpret it.

FOR DORMANT THREADS:
- Threads with high importance (7+) or must_resolve=true that go dormant are serious problems. The reader is waiting for these.
- Threads with low importance (1-3) going dormant is often fine — they're flavor, not load-bearing.
- Note whether the gap is long enough that the reader will have forgotten the thread by the time it reappears.
- Suggest specific chapters where a brief reminder (a line of dialogue, a visual callback) could keep the thread alive without derailing the scene.

FOR EVENT DENSITY:
- Flag chapters with zero or one event — these may be stalling the plot.
- Flag chapters with unusually high event counts — these may be rushing through material that deserves more space.
- Look for runs of low-density chapters in sequence — that's where the story sags.
- Look for runs of high-density chapters in sequence — that's where the reader gets exhausted.
- Note the overall shape: does event density build toward a climax, or is it random?

FOR SETUP-PAYOFF MAP:
- Setups with high emphasis (7+) and must_pay_off=true that have zero payoffs are broken promises. These are the most serious issues.
- Setups with only partial or reminder payoffs may need a stronger resolution.
- Note setups that pay off quickly (same chapter or next) vs. those that build over many chapters — both are valid but the balance matters.
- Flag any payoffs that seem to resolve setups too conveniently (full resolution immediately after a long gap with no reminders).

FORMAT:
Write 3-6 paragraphs of direct, actionable feedback. Lead with the most damaging issue — the thing most likely to lose readers. Reference specific chapter numbers throughout. For each problem, suggest a concrete fix: not "address this thread" but "add a two-line callback to the saboteur subplot in Chapter 9 dialogue to bridge the gap between Chapter 4 and Chapter 13."

End with what's working — which threads are well-managed, which setups pay off satisfyingly, which sections have good plot rhythm. Writers need to know what to protect during revisions."""


class PlotTrackerService:

    def __init__(self, mongodb: AsyncDatabase):
        self.mongodb = mongodb
        self._model = create_chat_model(app_config.ai_lite_model)

    @retry_mongo
    async def get_thread_timeline(
        self,
        story_id: str,
        user_id: str,
        thread_name: str,
    ) -> ThreadTimelineResponse:
        """Full lifecycle of a single thread across all chapters."""
        
        cursor = await self.mongodb.plot_extractions.aggregate([
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

        thread_states = [ ThreadState(**doc) async for doc in cursor ]

        return ThreadTimelineResponse(
            name=thread_name,
            states=thread_states
        )

    @retry_mongo
    async def get_dormant_threads(
        self,
        story_id: str,
        user_id: str,
        min_gap: int = 3,
    ) -> DormantThreadsResponse:
        """Threads that disappeared for min_gap+ consecutive chapters before reappearing."""
        
        # Step 1: Get all thread appearances grouped by thread name
        cursor = await self.mongodb.plot_extractions.aggregate([
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

        rows = [row async for row in cursor]

        # Step 2: Walk each thread's appearances and detect gaps
        dormant_threads: list[DormantThread] = []

        for row in rows:
            appearances = row["appearances"]

            if len(appearances) < 2:
                continue

            for i in range(len(appearances) - 1):
                current = appearances[i]
                next_app = appearances[i + 1]
                gap = next_app["chapter_number"] - current["chapter_number"] - 1

                if gap >= min_gap:
                    dormant_threads.append(
                        DormantThread(
                            name=row["_id"],
                            importance=current["importance"],
                            must_resolve=current["must_resolve"],
                            chapters_dormant=gap,
                            went_dormant_chapter_id=current["chapter_id"],
                            reappeared_chapter_id=next_app["chapter_id"],
                        )
                    )

        return DormantThreadsResponse(threads=dormant_threads)

    @retry_mongo
    async def get_event_density(
        self,
        story_id: str,
        user_id: str,
    ) -> EventDensityResponse:
        """Plot event count per chapter."""
        
        cursor = await self.mongodb.plot_extractions.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$unwind": "$events"},
            {"$group": {
                "_id": {"chapter_id": "$chapter_id", "chapter_number": "$chapter_number"},
                "event_count": {"$sum": 1}
            }},
            {"$sort": {"_id.chapter_number": 1}}
        ])

        event_counts = [
            ChapterEventCounts(
                chapter_id=doc["_id"]["chapter_id"],
                chapter_number=doc["_id"]["chapter_number"],
                num_events=doc["event_count"]
            )
            async for doc in cursor
        ]

        return EventDensityResponse(chapter_counts=event_counts)

    @retry_mongo
    async def get_setup_payoff_map(
        self,
        story_id: str,
        user_id: str,
    ) -> List[SetupPayoffMap]:
        """Every setup paired with its matching payoffs (or empty if unpaid)."""

        match = {"$match": {"story_id": story_id, "user_id": user_id}}

        # Get all setups
        setup_cursor = await self.mongodb.plot_extractions.aggregate([
            match,
            {"$unwind": "$setups"},
            {"$group": {
                "_id": "$setups.element",
                "emphasis": {"$max": "$setups.emphasis"},
                "must_pay_off": {"$max": "$setups.must_pay_off"},
            }}
        ])

        # Get all payoffs
        payoff_cursor = await self.mongodb.plot_extractions.aggregate([
            match,
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

        setups = [doc async for doc in setup_cursor]
        payoffs = [doc async for doc in payoff_cursor]

        # Group payoffs by element
        payoff_map: dict[str, list] = {}
        for p in payoffs:
            payoff_map.setdefault(p["element"], []).append(p)

        # Pair each setup with its payoffs
        return [
            SetupPayoffMap(
                element=setup["_id"],
                emphasis=setup["emphasis"],
                must_pay_off=setup["must_pay_off"],
                payoffs=[
                    PayoffState(
                        chapter_number=p["chapter_number"],
                        chapter_id=p["chapter_id"],
                        resolution=p["resolution"],
                    )
                    for p in payoff_map.get(setup["_id"], [])
                ]
            )
            for setup in setups
        ]


    @retry_mongo
    async def get_plot_density(
        self,
        story_id: str,
        user_id: str,
    ) -> PlotDensityResponse:
        """Per-chapter counts of events, setups, payoffs, and questions."""

        cursor = await self.mongodb.plot_extractions.aggregate([
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

        distributions = [
            ChapterPlotDistribution(**doc)
            async for doc in cursor
        ]

        return PlotDensityResponse(distributions=distributions)

    @retry_llm
    async def get_plot_rhythm_report(
        self,
        story_id: str,
        user_id: str,
    ) -> PlotRhythmReportResponse:
        """AI-generated report on plot pacing, thread management, and setup-payoff rhythm."""

        results = await asyncio.gather(
            self.get_dormant_threads(story_id, user_id),
            self.get_event_density(story_id, user_id),
            self.get_setup_payoff_map(story_id, user_id),
            return_exceptions=True
        )

        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Error generating plot rhythm report: {str(result)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="An error occurred while generating your report. Please try again later."
                )

        dormant_threads, event_density, setup_payoff_map = results

        response = await self._model.ainvoke([
            SystemMessage(content=PLOT_RHYTHM_REPORT_SYSTEM_PROMPT),
            HumanMessage(content=self._build_rhythm_report_prompt(
                dormant_threads, #type: ignore
                event_density, #type: ignore
                setup_payoff_map, #type: ignore
            ))
        ])

        return PlotRhythmReportResponse(
            story_id=story_id,
            report=extract_text(response.content)
        )

    def _build_rhythm_report_prompt(
        self,
        dormant: DormantThreadsResponse,
        density: EventDensityResponse,
        setup_payoff: List[SetupPayoffMap],
    ) -> str:

        dormant_lines = "\n".join(
            f"  - '{t.name}' [importance {t.importance}/10, must_resolve={t.must_resolve}] "
            f"— dormant for {t.chapters_dormant} chapters "
            f"(went dormant: chapter {t.went_dormant_chapter_id}, reappeared: chapter {t.reappeared_chapter_id})"
            for t in dormant.threads #type: ignore
        ) or "  None."

        density_lines = "\n".join(
            f"  - Chapter {c.chapter_number}: {c.num_events} events"
            for c in density.chapter_counts #type: ignore
        ) or "  None."

        setup_lines = "\n".join(
            f"  - '{s.element}' [emphasis {s.emphasis}/10, must_pay_off={s.must_pay_off}] — "
            + (
                ", ".join(
                    f"Ch.{p.chapter_number} ({p.resolution})"
                    for p in s.payoffs #type: ignore
                ) if s.payoffs else "NO PAYOFFS"
            )
            for s in setup_payoff
        ) or "  None."

        return f"""
DORMANT THREADS:
{dormant_lines}

EVENT DENSITY:
{density_lines}

SETUP-PAYOFF MAP:
{setup_lines}
"""


async def get_plot_tracker_service(
    mongodb: AsyncDatabase = Depends(get_mongodb)
) -> PlotTrackerService:
    return PlotTrackerService(mongodb=mongodb)