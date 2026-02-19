import asyncio

from fastapi import Depends, HTTPException, status
from langchain.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCommandCursor
from app.ai.models.plot import ContrivanceRisk, Payoff, PlotThread, Setup, StoryQuestion
from app.core.mongodb import get_mongodb
from app.schemas.plot import DeusExMachinaResponse, PlotStructuralReportResponse, PlotThreadsResponse, SetupResponse, StoryQuestionsResponse
from app.config.settings import app_config
from loguru import logger
from app.ai.prompts.plot import PLOT_STRUCTURAL_REPORT_PROMPT
from app.utils.ai import extract_text

class PlotService:

    def __init__(self, mongodb: AsyncIOMotorDatabase):
        self.mongodb = mongodb
        self._model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            temperature=app_config.ai_temperature,
            max_tokens=app_config.ai_maxtokens,
            timeout=app_config.ai_sdk_timeout,
            max_retries=app_config.ai_sdk_retries,
        )

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

        plot_threads_cursor: AsyncIOMotorCommandCursor = self.mongodb.plot_extractions.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$unwind": "$threads"},
            {"$match": {"threads.status": {"$ne": "resolved"}, "threads.must_resolve": True}},
            {"$replaceRoot": {"newRoot": "$threads"}}
        ])

        threads = [
            PlotThread(**thread) async for thread in plot_threads_cursor
        ]
        return PlotThreadsResponse(plot_threads=threads)
    
    async def get_all_unanswered_story_questions(self, user_id: str, story_id: str) -> StoryQuestionsResponse:     

        raised_questions_cursor: AsyncIOMotorCommandCursor = self.mongodb.plot_extractions.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$unwind": "$questions"},
            {"$match": {"questions.status": {"$eq": "raised"}, "questions.importance": {"$gte": 5}}},
            {"$replaceRoot": {"newRoot": "$questions"}}
        ])

        answered_questions_cursor: AsyncIOMotorCommandCursor = self.mongodb.plot_extractions.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$unwind": "$questions"},
            {"$match": {"questions.status": {"$eq": "answered"}, "questions.importance": {"$gte": 5}}},
            {"$replaceRoot": {"newRoot": "$questions"}}
        ])

        raised_questions = [
            StoryQuestion(**question) async for question in raised_questions_cursor
        ]

        answered_questions = {
            question["question"] async for question in answered_questions_cursor
        }

        unanswered_questions = [
            question for question in raised_questions if question.question not in answered_questions
        ]
        return StoryQuestionsResponse(questions=unanswered_questions)
    
    async def get_all_setups_with_no_payoffs(self, user_id: str, story_id: str) -> SetupResponse:

        match = {"$match": {"story_id": story_id, "user_id": user_id}}
        setups_cursor: AsyncIOMotorCommandCursor = self.mongodb.plot_extractions.aggregate([
            match,
            {"$unwind": "$setups"},
            {"$match": {"setups.must_pay_off": True}},
            {"$replaceRoot": {"newRoot": "$setups"}}
        ])

        payoffs_cursor: AsyncIOMotorCommandCursor = self.mongodb.plot_extractions.aggregate([
            match,
            {"$unwind": "$payoffs"},
            {"$replaceRoot": {"newRoot": "$payoffs"}}
        ])

        setups = [Setup(**s) async for s in setups_cursor]
        payoffs = [Payoff(**p) async for p in payoffs_cursor]

        paid_off_elements = {p.element for p in payoffs if p.resolution == "full"}
        unresolved = [s for s in setups if s.element not in paid_off_elements]

        return SetupResponse(setups=unresolved)
    
    async def get_all_deus_ex_machinas(self, user_id: str, story_id: str) -> DeusExMachinaResponse:
    
        dues_ex_machina_cursor: AsyncIOMotorCommandCursor = self.mongodb.plot_extractions.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$unwind": "$contrivance_risks"},
            {"$match": {"$or": [
                {"contrivance_risks.risk": {"$gte": 7}},
                {"contrivance_risks.has_prior_setup": False}
            ]}},
            {"$replaceRoot": {"newRoot": "$contrivance_risks"}} 
        ])
        dues_ex_machinas = [
            ContrivanceRisk(**problem) async for problem in dues_ex_machina_cursor
        ]
        return DeusExMachinaResponse(problems=dues_ex_machinas)
    
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
                logger.warning(f"Error generating structural report: {str(result)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="An error occurred while generating your report. Please try again later."
                )

        # Unpack only after checking for exceptions
        threads, questions, setups, contrivances = results

        response = await self._model.ainvoke([
            SystemMessage(content=PLOT_STRUCTURAL_REPORT_PROMPT),
            HumanMessage(content=self._build_structural_report_prompt(
                threads, #type: ignore
                questions, #type: ignore
                setups, #type: ignore
                contrivances #type: ignore
            )) 
        ])

        return PlotStructuralReportResponse(
            story_id=story_id, 
            report=extract_text(response)
        )
        
    
def get_plot_service(
    mongodb: AsyncIOMotorDatabase = Depends(get_mongodb)
) -> PlotService:
    return PlotService(mongodb=mongodb)