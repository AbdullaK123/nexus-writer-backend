from typing import List, Optional
from pydantic import BaseModel
from app.ai.models.plot import ContrivanceRisk, PlotThread, Setup, StoryQuestion

class PlotThreadsResponse(BaseModel):
    plot_threads: Optional[List[PlotThread]] = []

class StoryQuestionsResponse(BaseModel):
    questions: Optional[List[StoryQuestion]] = []

class SetupResponse(BaseModel):
    setups: Optional[List[Setup]] = []

class DeusExMachinaResponse(BaseModel):
    problems: Optional[List[ContrivanceRisk]] = []

class PlotStructuralReportResponse(BaseModel):
    story_id: str
    report: str = ""