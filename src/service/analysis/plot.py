import asyncio
import time

from src.service.exceptions import InternalError
from langchain.messages import HumanMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel
from src.data.models.ai.plot import ContrivanceRisk, Payoff, PlotThread, Setup, StoryQuestion
from src.data.schemas.plot import DeusExMachinaResponse, PlotStructuralReportResponse, PlotThreadsResponse, SetupResponse, StoryQuestionsResponse
from src.shared.utils.logging_context import get_layer_logger, LAYER_SERVICE

log = get_layer_logger(LAYER_SERVICE)
from src.service.ai.prompts.plot import PLOT_STRUCTURAL_REPORT_PROMPT
from src.service.ai.utils.ai import extract_text
from src.infrastructure.utils.retry import retry_llm
from src.data.repositories.mongo.plot_extraction import PlotExtractionRepo

class PlotService:

    def __init__(self, repo: PlotExtractionRepo, model: BaseChatModel):
        self.repo = repo
        self._model = model

    def _build_structural_report_prompt(
        self,
        threads: PlotThreadsResponse,
        questions: StoryQuestionsResponse,
        setups: SetupResponse,
        contrivances: DeusExMachinaResponse
    ) -> str:

        unresolved_threads = "\n".join(
            f"  - [{t.importance}/10] '{t.name}' (status: {t.status})"
            for t in threads.plot_threads #type: ignore
        ) or "  None."

        unanswered_questions = "\n".join(
            f"  - [{q.importance}/10] {q.question}"
            for q in questions.questions #type: ignore
        ) or "  None."

        unpaid_setups = "\n".join(
            f"  - [emphasis {s.emphasis}/10] '{s.element}'"
            for s in setups.setups #type: ignore
        ) or "  None."

        contrivance_risks = "\n".join(
            f"  - [risk {c.risk}/10, prior setup: {c.has_prior_setup}]\n"
            f"    Problem: {c.problem}\n"
            f"    Solution used: {c.solution}"
            for c in contrivances.problems #type: ignore
        ) or "  None."

        return f"""
        UNRESOLVED PLOT THREADS (must_resolve=True):
        {unresolved_threads}

        UNANSWERED STORY QUESTIONS (importance >= 5):
        {unanswered_questions}

        SETUPS WITH NO PAYOFF (must_pay_off=True):
        {unpaid_setups}

        HIGH-RISK CONTRIVANCES (risk >= 7 or no prior setup):
        {contrivance_risks}
        """

    async def get_all_unresolved_plot_threads(self, user_id: str, story_id: str) -> PlotThreadsResponse: 
        rows = await self.repo.get_unresolved_threads(story_id, user_id)
        threads = [PlotThread(**thread) for thread in rows]
        return PlotThreadsResponse(plot_threads=threads)
    
    async def get_all_unanswered_story_questions(self, user_id: str, story_id: str) -> StoryQuestionsResponse:     
        raised = await self.repo.get_raised_questions(story_id, user_id)
        answered = await self.repo.get_answered_questions(story_id, user_id)

        raised_questions = [StoryQuestion(**question) for question in raised]
        answered_set = {q["question"] for q in answered}

        unanswered_questions = [
            question for question in raised_questions if question.question not in answered_set
        ]
        return StoryQuestionsResponse(questions=unanswered_questions)
    
    async def get_all_setups_with_no_payoffs(self, user_id: str, story_id: str) -> SetupResponse:
        setup_rows = await self.repo.get_must_pay_off_setups(story_id, user_id)
        payoff_rows = await self.repo.get_all_payoffs(story_id, user_id)

        setups = [Setup(**s) for s in setup_rows]
        payoffs = [Payoff(**p) for p in payoff_rows]

        paid_off_elements = {p.element for p in payoffs if p.resolution == "full"}
        unresolved = [s for s in setups if s.element not in paid_off_elements]

        return SetupResponse(setups=unresolved)
    
    async def get_all_deus_ex_machinas(self, user_id: str, story_id: str) -> DeusExMachinaResponse:
        rows = await self.repo.get_high_risk_contrivances(story_id, user_id)
        problems = [ContrivanceRisk(**problem) for problem in rows]
        return DeusExMachinaResponse(problems=problems)
    
    @retry_llm
    async def get_structural_report(
        self,
        story_id: str,
        user_id: str
    ) -> PlotStructuralReportResponse:
        
        results = await asyncio.gather(
            self.get_all_unresolved_plot_threads(user_id, story_id),
            self.get_all_unanswered_story_questions(user_id, story_id),
            self.get_all_setups_with_no_payoffs(user_id, story_id),
            self.get_all_deus_ex_machinas(user_id, story_id),
            return_exceptions=True
        )

        for result in results:
            if isinstance(result, Exception):
                log.warning("analysis.structural_report.data_failed", story_id=story_id, error=str(result))
                raise InternalError("An error occurred while generating your report. Please try again later.")

        # Unpack only after checking for exceptions
        threads, questions, setups, contrivances = results

        log.info("analysis.structural_report.start", story_id=story_id)
        t0 = time.perf_counter()
        try:
            response = await self._model.ainvoke([
                SystemMessage(content=PLOT_STRUCTURAL_REPORT_PROMPT),
                HumanMessage(content=self._build_structural_report_prompt(
                    threads, #type: ignore
                    questions, #type: ignore
                    setups, #type: ignore
                    contrivances #type: ignore
                )) 
            ])
        except Exception:
            log.opt(exception=True).error(
                "analysis.structural_report.error", story_id=story_id,
                elapsed_s=round(time.perf_counter() - t0, 2),
            )
            raise
        elapsed = round(time.perf_counter() - t0, 2)
        log.info(
            "analysis.structural_report.done", story_id=story_id,
            elapsed_s=elapsed, tokens=getattr(response, 'usage_metadata', None),
        )

        return PlotStructuralReportResponse(
            story_id=story_id, 
            report=extract_text(response.content)
        )
        
    

