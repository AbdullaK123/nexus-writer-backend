from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCommandCursor
from app.ai.models.plot import ContrivanceRisk, Payoff, PlotThread, Setup, StoryQuestion
from app.core.mongodb import get_mongodb
from app.schemas.plot import DeusExMachinaResponse, PlotThreadsResponse, SetupResponse, StoryQuestionsResponse

class PlotService:

    def __init__(self, mongodb: AsyncIOMotorDatabase):
        self.mongodb = mongodb

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
    
def get_plot_service(
    mongodb: AsyncIOMotorDatabase = Depends(get_mongodb)
) -> PlotService:
    return PlotService(mongodb=mongodb)