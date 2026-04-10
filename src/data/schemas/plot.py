from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from src.service.ai.models.plot import ContrivanceRisk, PlotThread, Setup, StoryQuestion

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

class ThreadState(BaseModel):
    chapter_id: str
    chapter_number: int
    status: Literal["introduced", "active", "resolved", "dormant"]
    importance: int = Field(ge=1, le=10, description="Narrative weight: 1-3 = flavor/atmosphere detail, 4-6 = meaningful subplot, 7-9 = major storyline, 10 = THE central plot")
    must_resolve: bool = Field(description="True if this thread has been given enough narrative weight that leaving it unresolved would feel like a plot hole or broken promise to the reader. Once set to True for a thread, it should remain True in subsequent chapters unless the thread is resolved.")

class ThreadTimelineResponse(BaseModel):
    name: str
    states: Optional[List[ThreadState]] = []


class DormantThread(BaseModel):
    name: str 
    importance: int = Field(ge=1, le=10, description="Narrative weight: 1-3 = flavor/atmosphere detail, 4-6 = meaningful subplot, 7-9 = major storyline, 10 = THE central plot")
    must_resolve: bool = Field(description="True if this thread has been given enough narrative weight that leaving it unresolved would feel like a plot hole or broken promise to the reader. Once set to True for a thread, it should remain True in subsequent chapters unless the thread is resolved.")
    chapters_dormant: int 
    went_dormant_chapter_id: str 
    reappeared_chapter_id: str 

class DormantThreadsResponse(BaseModel):
    threads: Optional[List[DormantThread]] = []

class ChapterEventCounts(BaseModel):
    chapter_number: int 
    chapter_id: str 
    num_events: int 

class EventDensityResponse(BaseModel):
    chapter_counts: Optional[List[ChapterEventCounts]] = []

class PayoffState(BaseModel):
    chapter_number: int 
    chapter_id: str 
    resolution: Literal["full", "partial", "reminder"]

class SetupPayoffMap(BaseModel):
    element: str
    emphasis: int = Field(ge=1, le=10)
    must_pay_off: bool
    payoffs: Optional[List[PayoffState]] = []

class ChapterPlotDistribution(BaseModel):
    chapter_number: int 
    chapter_id: str 
    event_count: int 
    setup_count: int 
    payoff_count: int 
    question_count: int 

class PlotDensityResponse(BaseModel):
    distributions: Optional[List[ChapterPlotDistribution]] = []

class PlotRhythmReportResponse(BaseModel):
    story_id: str
    report: str = ""
