from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Optional, Literal
from datetime import datetime


class PlotThreadStatus(BaseModel):
    """Current status of a plot thread"""
    status: Literal["active", "resolved", "abandoned", "dormant"] = Field(
        description="Current state of the plot thread"
    )
    last_mentioned_chapter: int = Field(
        description="Most recent chapter where this thread appeared"
    )
    chapters_since_mention: int = Field(
        default=0,
        description="Number of chapters since last mention (for dormancy tracking)"
    )


class PlotThreadObstacle(BaseModel):
    """An obstacle or complication in a plot thread"""
    obstacle: str = Field(description="Description of the obstacle")
    introduced_chapter: int = Field(description="When this obstacle first appeared")
    resolved_chapter: Optional[int] = Field(
        default=None,
        description="When this obstacle was overcome (null if still active)"
    )
    resolution: Optional[str] = Field(
        default=None,
        description="How the obstacle was resolved"
    )


class PlotThreadTwist(BaseModel):
    """A major revelation or twist in the plot thread"""
    chapter: int = Field(description="Chapter where twist occurred")
    twist: str = Field(description="Description of the twist/revelation")
    impact: str = Field(description="How this changed the direction of the thread")


class StoryQuestion(BaseModel):
    """A question raised or answered by the narrative"""
    question: str = Field(description="The story question")
    raised_chapter: int = Field(description="When this question was first raised")
    answered_chapter: Optional[int] = Field(
        default=None,
        description="When this question was answered (null if unanswered)"
    )
    answer: Optional[str] = Field(
        default=None,
        description="The answer provided by the story"
    )
    importance: Literal["critical", "major", "minor"] = Field(
        description="How important this question is to the overall story"
    )


class PlotThread(BaseModel):
    """A single plot thread/storyline"""
    
    thread_id: str = Field(description="Unique identifier for this thread (e.g., 'main_conspiracy')")
    
    name: str = Field(description="Short name for the plot thread")
    
    thread_type: Literal["main", "subplot", "character_arc", "mystery", "romance"] = Field(
        description="Category of plot thread"
    )
    
    description: str = Field(
        description="2-3 sentence description of what this thread is about"
    )
    
    status: PlotThreadStatus = Field(description="Current status of the thread")
    
    introduced_chapter: int = Field(description="Chapter where thread was introduced")
    
    resolved_chapter: Optional[int] = Field(
        default=None,
        description="Chapter where thread was resolved (null if still active)"
    )
    
    key_chapters: List[int] = Field(
        default=[],
        description="Chapters where significant developments occurred"
    )
    
    # Story stakes and goals
    stakes: str = Field(
        description="What's at risk if this thread fails? What are the consequences?"
    )
    
    goal: str = Field(
        description="What needs to be achieved to resolve this thread?"
    )
    
    # Characters involved
    primary_characters: List[str] = Field(
        default=[],
        description="Main characters driving this plot thread"
    )
    
    supporting_characters: List[str] = Field(
        default=[],
        description="Characters involved but not driving the thread"
    )
    
    # Complications and progression
    obstacles: List[PlotThreadObstacle] = Field(
        default=[],
        description="Obstacles that complicate this thread"
    )
    
    twists: List[PlotThreadTwist] = Field(
        default=[],
        description="Major twists or revelations in this thread"
    )
    
    # Story questions
    questions_raised: List[StoryQuestion] = Field(
        default=[],
        description="Questions this thread introduces"
    )
    
    # Foreshadowing and setup
    foreshadowing: List[str] = Field(
        default=[],
        description="Elements that foreshadow future developments in this thread"
    )
    
    setup_chapters: List[int] = Field(
        default=[],
        description="Chapters that set up future payoffs in this thread"
    )
    
    payoff_chapters: List[int] = Field(
        default=[],
        description="Chapters that pay off earlier setups"
    )
    
    # Resolution details (if resolved)
    resolution_summary: Optional[str] = Field(
        default=None,
        description="How this thread was resolved (2-3 sentences)"
    )
    
    resolution_satisfaction: Optional[Literal["satisfying", "rushed", "anticlimactic", "unresolved"]] = Field(
        default=None,
        description="Assessment of how well this thread was resolved"
    )
    
    # Connections to other threads
    related_threads: List[str] = Field(
        default=[],
        description="IDs of other plot threads this one intersects with"
    )
    
    # Pacing analysis
    pacing_notes: Optional[str] = Field(
        default=None,
        description="Notes on pacing - is this thread advancing too fast/slow?"
    )


class PlotThreadIntersection(BaseModel):
    """Where two plot threads intersect or influence each other"""
    thread_1_id: str = Field(description="ID of first thread")
    thread_2_id: str = Field(description="ID of second thread")
    intersection_chapter: int = Field(description="Chapter where they intersect")
    interaction_type: Literal["collision", "merger", "complication", "resolution"] = Field(
        description="How the threads interact"
    )
    description: str = Field(
        description="How these threads affect each other"
    )


class PlotThreadWarning(BaseModel):
    """Potential issues with plot threads"""
    thread_id: str = Field(description="ID of the problematic thread")
    warning_type: Literal["dormant", "rushed", "dangling", "contradictory", "overstuffed"] = Field(
        description="Type of potential issue"
    )
    severity: Literal["minor", "moderate", "major"] = Field(
        description="How serious this issue is"
    )
    description: str = Field(
        description="Explanation of the issue"
    )
    recommendation: str = Field(
        description="Suggested fix for the issue"
    )


class PlotThreadsExtraction(BaseModel):
    """
    Complete plot thread analysis for a story.
    
    Tracks all storylines, their status, progression, and relationships.
    Generated by analyzing all chapter extractions and story context.
    """
    
    threads: Dict[str, PlotThread] = Field(
        description="Map of thread_id to PlotThread object"
    )
    
    # High-level statistics
    total_threads: int = Field(description="Total number of plot threads")
    
    active_threads: List[str] = Field(
        description="Thread IDs that are currently active"
    )
    
    resolved_threads: List[str] = Field(
        description="Thread IDs that have been resolved"
    )
    
    dormant_threads: List[str] = Field(
        description="Thread IDs that haven't been mentioned in 5+ chapters"
    )
    
    abandoned_threads: List[str] = Field(
        description="Thread IDs that were introduced but never developed/resolved"
    )
    
    # Thread structure analysis
    main_threads: List[str] = Field(
        description="Thread IDs of main plot threads"
    )
    
    subplots: List[str] = Field(
        description="Thread IDs of subplots"
    )
    
    character_arcs: List[str] = Field(
        description="Thread IDs that are character-focused arcs"
    )
    
    # Story questions
    unanswered_questions: List[StoryQuestion] = Field(
        default=[],
        description="All story questions that remain unanswered"
    )
    
    answered_questions: List[StoryQuestion] = Field(
        default=[],
        description="All story questions that have been answered"
    )
    
    # Thread interactions
    thread_intersections: List[PlotThreadIntersection] = Field(
        default=[],
        description="Where plot threads intersect or influence each other"
    )
    
    # Issues and warnings
    warnings: List[PlotThreadWarning] = Field(
        default=[],
        description="Potential issues with plot threads"
    )
    
    # Narrative structure insights
    convergence_chapter: Optional[int] = Field(
        default=None,
        description="Chapter where most threads converge (typically climax)"
    )
    
    threads_per_chapter: Dict[int, List[str]] = Field(
        default={},
        description="Map of chapter number to active thread IDs"
    )
    
    # Overall assessment
    plot_complexity_score: int = Field(
        ge=1,
        le=10,
        description="How complex is the plot? (1=simple, 10=extremely complex)"
    )
    
    plot_coherence_score: int = Field(
        ge=1,
        le=10,
        description="How well do threads weave together? (1=disjointed, 10=masterfully woven)"
    )
    
    pacing_balance: Literal["too_slow", "well_paced", "too_fast", "uneven"] = Field(
        description="Overall assessment of plot pacing"
    )
    
    narrative_summary: str = Field(
        description="2-3 sentence overview of how all threads work together"
    )
    
    generated_at: datetime = Field(
        default_factory=datetime.now,
        description="When this extraction was generated"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "threads": {
                    "main_conspiracy": {
                        "thread_id": "main_conspiracy",
                        "name": "The Alien Conspiracy",
                        "thread_type": "main",
                        "description": "Discovery of alien artifact leads to uncovering fleet-wide conspiracy involving highest ranks",
                        "status": {
                            "status": "active",
                            "last_mentioned_chapter": 25,
                            "chapters_since_mention": 0
                        },
                        "introduced_chapter": 3,
                        "resolved_chapter": None,
                        "key_chapters": [3, 7, 12, 18, 25],
                        "stakes": "Survival of entire fleet and exposure of military corruption",
                        "goal": "Expose conspiracy, secure artifact, clear Vex's name",
                        "primary_characters": ["Commander Vex", "Admiral Kora"],
                        "obstacles": [
                            {
                                "obstacle": "Admiral blocking investigation",
                                "introduced_chapter": 7,
                                "resolved_chapter": 27,
                                "resolution": "Admiral exposed and removed from command"
                            }
                        ],
                        "questions_raised": [
                            {
                                "question": "Who planted the artifact?",
                                "raised_chapter": 5,
                                "answered_chapter": None,
                                "answer": None,
                                "importance": "critical"
                            }
                        ]
                    }
                },
                "total_threads": 8,
                "active_threads": ["main_conspiracy", "vex_chen_romance"],
                "unanswered_questions": [...],
                "warnings": [
                    {
                        "thread_id": "missing_crew_subplot",
                        "warning_type": "dormant",
                        "severity": "moderate",
                        "description": "Thread hasn't been mentioned in 8 chapters",
                        "recommendation": "Either resolve or reintroduce in next 2-3 chapters"
                    }
                ]
            }
        }
    )