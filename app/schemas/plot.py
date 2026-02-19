from typing import List, Optional
from sqlmodel import SQLModel
from app.ai.models.plot import ContrivanceRisk, PlotThread, Setup, StoryQuestion

class PlotThreadsResponse(SQLModel):
    plot_threads: Optional[List[PlotThread]] = []

class StoryQuestionsResponse(SQLModel):
    questions: Optional[List[StoryQuestion]] = []

class SetupResponse(SQLModel):
    setups: Optional[List[Setup]] = []

class DeusExMachinaResponse(SQLModel):
    problems: Optional[List[ContrivanceRisk]] = []

class PlotStructuralReportResponse(SQLModel):
    story_id: str
    report: str = ""