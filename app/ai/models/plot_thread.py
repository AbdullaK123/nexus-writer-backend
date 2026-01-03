from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class PlotThread(BaseModel):
    """A single plot thread/storyline"""
    
    thread_id: str = Field(description="Unique identifier (e.g., 'main_conspiracy')")
    name: str = Field(description="Short name for the plot thread")
    thread_type: Literal["main", "subplot", "character_arc", "mystery", "romance"]
    description: str = Field(description="What this thread is about")
    
    status: Literal["active", "resolved", "abandoned", "dormant"]
    introduced_chapter: int
    resolved_chapter: Optional[int] = None
    
    stakes: str = Field(description="What's at risk?")
    goal: str = Field(description="What needs to be achieved?")
    
    primary_characters: List[str] = Field(default=[])
    key_chapters: List[int] = Field(default=[], description="Major developments")
    
    resolution_summary: Optional[str] = None


class StoryQuestion(BaseModel):
    """A question raised or answered by the narrative"""
    question: str
    raised_chapter: int
    answered_chapter: Optional[int] = None
    answer: Optional[str] = None
    importance: Literal["critical", "major", "minor"]


class PlotThreadWarning(BaseModel):
    """Potential issues with plot threads"""
    thread_id: str
    warning_type: Literal["dormant", "rushed", "dangling", "contradictory"]
    severity: Literal["minor", "moderate", "major"]
    description: str
    recommendation: str


class PlotThreadsExtraction(BaseModel):
    """Complete plot thread analysis for a story"""
    
    threads: List[PlotThread] = Field(description="All plot threads in the story")
    
    total_threads: int
    active_thread_ids: List[str] = Field(default=[])
    resolved_thread_ids: List[str] = Field(default=[])
    
    unanswered_questions: List[StoryQuestion] = Field(default=[])
    warnings: List[PlotThreadWarning] = Field(default=[])
    
    plot_complexity_score: int = Field(ge=1, le=10, description="1=simple, 10=complex")
    plot_coherence_score: int = Field(ge=1, le=10, description="How well threads weave together")
    
    narrative_summary: str = Field(description="Overview of how all threads work together")
    
    generated_at: datetime = Field(default_factory=datetime.now)