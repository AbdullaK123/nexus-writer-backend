from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlmodel.ext.asyncio.session import AsyncSession
from app.schemas.plot import DeusExMachinaResponse, PlotThreadsResponse, SetupResponse, StoryQuestionsResponse

class PlotService:

    def __init__(self, db: AsyncSession, mongodb: AsyncIOMotorDatabase):
        self.db = db
        self.mongodb = mongodb

    async def get_all_unresolved_plot_threads(self, user_id: str, story_id: str) -> PlotThreadsResponse:
        #TODO: gets all unresolved plot threads
        return PlotThreadsResponse()
    
    async def get_all_unanswered_story_questions(self, user_id: str, story_id: str) -> StoryQuestionsResponse:
        #TODO: gets all unanswered story questions
        return StoryQuestionsResponse()
    
    async def get_all_setups_with_no_payoffs(self, user_id: str, story_id: str) -> SetupResponse:
        #TODO: gets all setups with no payoffs
        return SetupResponse()
    
    async def get_all_dues_ex_machinas(self, user_id: str, story_id: str) -> DeusExMachinaResponse:
        #TODOL gets all dues ex machinas
        return DeusExMachinaResponse()
    
