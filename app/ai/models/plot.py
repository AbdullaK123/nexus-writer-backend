from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from app.ai.models.enums import PlotThreadStatus

class PlotEvent(BaseModel):
    """A significant event in the chapter"""
    sequence_number: int = Field(description="Order within chapter (1, 2, 3...)")
    event: str = Field(description="What happened")
    participants: List[str] = Field(description="Characters involved")
    location: str
    outcome: str = Field(description="Immediate result")
    significance: str = Field(description="Why this matters to the story")


class CausalChain(BaseModel):
    """Cause and effect relationship"""
    cause_event: str
    effect_event: str
    chapter_numbers: List[int] = Field(
        description="Chapters involved (cause might be from earlier chapter)"
    )


class PlotThread(BaseModel):
    """A storyline thread"""
    thread_name: str = Field(description="Name of this plot thread")
    status: PlotThreadStatus
    description: str = Field(description="What's happening with this thread")
    characters_involved: List[str]
    introduced_chapter: Optional[int] = Field(None, description="When this thread started")


class StoryQuestion(BaseModel):
    """Question raised or answered"""
    question: str
    raised_or_answered: Literal["raised", "answered"]
    related_plot_threads: List[str] = Field(default_factory=list)


class ForeshadowingElement(BaseModel):
    """Setup for future payoff"""
    element: str = Field(description="What was set up")
    type: Literal["chekovs_gun", "hint", "promise", "prophecy"]
    subtlety: Literal["obvious", "moderate", "subtle"]
    

class CallbackElement(BaseModel):
    """Reference to earlier setup"""
    callback: str = Field(description="What was referenced")
    original_chapter: int = Field(description="Chapter where it was set up")
    payoff_type: Literal["full_resolution", "partial_payoff", "reminder"]


class PlotExtraction(BaseModel):
    """All plot-related information from a chapter"""
    events: List[PlotEvent]
    causal_chains: List[CausalChain]
    plot_threads: List[PlotThread]
    story_questions: List[StoryQuestion]
    foreshadowing: List[ForeshadowingElement]
    callbacks: List[CallbackElement]

class ChapterPlotExtraction(BaseModel):
    chapter_id: str
    story_id: str
    chapter_number: int
    events: List[PlotEvent]
    causal_chains: List[CausalChain]
    plot_threads: List[PlotThread]
    story_questions: List[StoryQuestion]
    foreshadowing: List[ForeshadowingElement]
    callbacks: List[CallbackElement]