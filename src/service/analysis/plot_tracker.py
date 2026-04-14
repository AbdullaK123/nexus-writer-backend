import asyncio
from typing import List
from src.service.exceptions import InternalError
from langchain.messages import HumanMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel
from src.shared.utils.logging_context import get_layer_logger, LAYER_SERVICE

log = get_layer_logger(LAYER_SERVICE)
from src.data.schemas.plot import *
from src.service.ai.utils.ai import extract_text
from src.infrastructure.utils.retry import retry_llm
from src.data.repositories.mongo.plot_extraction import PlotExtractionRepo


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

    def __init__(self, repo: PlotExtractionRepo, model: BaseChatModel):
        self.repo = repo
        self._model = model

    async def get_thread_timeline(
        self,
        story_id: str,
        user_id: str,
        thread_name: str,
    ) -> ThreadTimelineResponse:
        """Full lifecycle of a single thread across all chapters."""
        rows = await self.repo.get_thread_timeline(story_id, user_id, thread_name)
        thread_states = [ThreadState(**doc) for doc in rows]
        return ThreadTimelineResponse(name=thread_name, states=thread_states)

    async def get_dormant_threads(
        self,
        story_id: str,
        user_id: str,
        min_gap: int = 3,
    ) -> DormantThreadsResponse:
        """Threads that disappeared for min_gap+ consecutive chapters before reappearing."""
        rows = await self.repo.get_thread_appearances(story_id, user_id)

        # Walk each thread's appearances and detect gaps
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

    async def get_event_density(
        self,
        story_id: str,
        user_id: str,
    ) -> EventDensityResponse:
        """Plot event count per chapter."""
        rows = await self.repo.get_event_counts(story_id, user_id)

        event_counts = [
            ChapterEventCounts(
                chapter_id=doc["_id"]["chapter_id"],
                chapter_number=doc["_id"]["chapter_number"],
                num_events=doc["event_count"]
            )
            for doc in rows
        ]

        return EventDensityResponse(chapter_counts=event_counts)

    async def get_setup_payoff_map(
        self,
        story_id: str,
        user_id: str,
    ) -> List[SetupPayoffMap]:
        """Every setup paired with its matching payoffs (or empty if unpaid)."""
        setups = await self.repo.get_setup_elements(story_id, user_id)
        payoffs = await self.repo.get_payoff_details(story_id, user_id)

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

    async def get_plot_density(
        self,
        story_id: str,
        user_id: str,
    ) -> PlotDensityResponse:
        """Per-chapter counts of events, setups, payoffs, and questions."""
        rows = await self.repo.get_plot_density(story_id, user_id)
        distributions = [ChapterPlotDistribution(**doc) for doc in rows]
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
                log.warning(f"Error generating plot rhythm report: {str(result)}")
                raise InternalError("An error occurred while generating your report. Please try again later.")

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



