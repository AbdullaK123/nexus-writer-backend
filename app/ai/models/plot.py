from typing import List, Literal, Optional, Dict
from pydantic import BaseModel, Field
from app.ai.models.enums import PlotThreadStatus
from uuid import uuid4


# ============================================================================
# OPTIMIZED FOR: Plot Hole Detection & Causal Logic
# ============================================================================

class InformationReveal(BaseModel):
    """Tracks who learns what - critical for plot hole detection"""
    info_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique ID for this information")
    information: str = Field(description="The information revealed")
    revealed_to: List[str] = Field(description="Characters who learned this")
    revealed_by: Optional[str] = Field(None, description="Who/what revealed it")
    reveal_method: str = Field(
        description="witnessed, overheard, told directly, discovered, deduced"
    )
    reliability: Literal["certain", "uncertain", "misleading"] = Field(
        default="certain",
        description="Is this information true?"
    )
    
    # For plot hole detection:
    # Query: "Character acts on info_id X but wasn't in revealed_to list"


class PlotEvent(BaseModel):
    """A significant event in the chapter - enhanced with causality tracking"""
    event_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique event ID")
    sequence_number: int = Field(description="Order within chapter (1, 2, 3...)")
    event: str = Field(description="What happened")
    participants: List[str] = Field(description="Characters involved")
    location: str
    
    # Causality tracking
    caused_by_event_ids: List[str] = Field(
        default_factory=list,
        description="Event IDs that led to this (from same or prior chapters)"
    )
    enables_future_events: List[str] = Field(
        default_factory=list,
        description="Event IDs this makes possible (filled retroactively)"
    )
    
    # Character motivation
    character_motivations: Dict[str, str] = Field(
        default_factory=dict,
        description="Key: character name, Value: why they acted"
    )
    
    outcome: str = Field(description="Immediate result")
    significance: str = Field(description="Why this matters to the story")
    information_revealed: List[InformationReveal] = Field(
        default_factory=list,
        description="Information disclosed during this event"
    )
    
    # For causality checking:
    # Query: "Events with no caused_by_event_ids (potential deus ex machina)"


class CausalChain(BaseModel):
    """Cause and effect relationship - enhanced"""
    chain_id: str = Field(default_factory=lambda: str(uuid4()))
    cause_event_id: str = Field(description="Event ID that caused")
    cause_description: str = Field(description="What caused it")
    effect_event_id: str = Field(description="Event ID of effect")
    effect_description: str = Field(description="What resulted")
    logical_strength: Literal["strong", "plausible", "weak", "questionable"] = Field(
        description="How logical is this connection?"
    )
    chapter_span: List[int] = Field(
        description="Chapters involved (e.g., [5, 12] = cause in ch5, effect in ch12)"
    )


# ============================================================================
# OPTIMIZED FOR: Abandoned Plot Thread Detection
# ============================================================================

class PlotThread(BaseModel):
    """A storyline thread - enhanced with abandonment tracking"""
    thread_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique thread ID")
    thread_name: str = Field(description="Name of this plot thread")
    status: PlotThreadStatus
    description: str = Field(description="What's happening with this thread")
    characters_involved: List[str]
    
    # Abandonment tracking
    introduced_chapter: int = Field(description="When this thread started")
    last_mentioned_chapter: int = Field(description="Most recent chapter it appeared")
    importance_level: int = Field(
        ge=1, le=10,
        description="1=minor subplot, 10=main plot. Higher = needs resolution!"
    )
    must_resolve: bool = Field(
        default=True,
        description="Does this NEED payoff, or is it just background/flavor?"
    )
    resolution_expected: Optional[int] = Field(
        None,
        description="Chapter where resolution is expected (if foreshadowed)"
    )
    
    # For abandonment detection:
    # Query: "Threads with importance > 5, last_mentioned_chapter < current - 5, must_resolve=True"


class StoryQuestion(BaseModel):
    """Question raised or answered - tracks mysteries"""
    question_id: str = Field(default_factory=lambda: str(uuid4()))
    question: str
    raised_or_answered: Literal["raised", "answered", "partially_answered"]
    related_plot_threads: List[str] = Field(
        default_factory=list,
        description="Thread IDs this question relates to"
    )
    importance: int = Field(
        ge=1, le=10,
        description="How important is this question? Major mysteries = 10"
    )
    raised_in_chapter: Optional[int] = Field(None, description="When was this asked?")
    answered_in_chapter: Optional[int] = Field(None, description="When was this answered?")
    
    # For tracking:
    # Query: "Questions with raised_or_answered='raised', importance > 7, still open"


# ============================================================================
# OPTIMIZED FOR: Chekhov's Gun Tracking (Setup/Payoff)
# ============================================================================

class ForeshadowingElement(BaseModel):
    """Setup for future payoff - with linking capability"""
    foreshadowing_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique ID for matching to payoffs")
    element: str = Field(description="What was set up")
    type: Literal["chekovs_gun", "hint", "promise", "prophecy", "planted_clue"]
    subtlety: Literal["obvious", "moderate", "subtle"]
    
    # Payoff tracking
    emphasis_level: int = Field(
        ge=1, le=10,
        description="How much attention was drawn? High emphasis MUST pay off!"
    )
    must_pay_off: bool = Field(
        description="True for Chekhov's guns (emphasized objects/abilities that MUST be used)"
    )
    expected_payoff_timeframe: Optional[str] = Field(
        None,
        description="soon, mid-story, climax, or specific chapter range"
    )
    characters_aware: List[str] = Field(
        default_factory=list,
        description="Which characters know about this?"
    )
    
    # For Chekhov's gun detection:
    # Query: "Foreshadowing with must_pay_off=True, emphasis > 7, no matching callback"


class CallbackElement(BaseModel):
    """Reference to earlier setup - with linking"""
    callback_id: str = Field(default_factory=lambda: str(uuid4()))
    callback: str = Field(description="What was referenced/paid off")
    foreshadowing_id: Optional[str] = Field(
        None,
        description="Links back to ForeshadowingElement.foreshadowing_id"
    )
    original_chapter: int = Field(description="Chapter where it was set up")
    payoff_type: Literal["full_resolution", "partial_payoff", "reminder", "twist"]
    satisfying: bool = Field(
        description="Was this a satisfying payoff? (AI judgment)"
    )
    
    # For matching:
    # Query: "JOIN foreshadowing on foreshadowing_id to validate all guns fired"


# ============================================================================
# OPTIMIZED FOR: Deus Ex Machina Detection
# ============================================================================

class DeusExMachinaRisk(BaseModel):
    """Potential deus ex machina - solution appearing from nowhere"""
    solution_description: str = Field(description="What solved the problem")
    problem_solved: str
    risk_level: Literal["high", "medium", "low"]
    why_risky: str = Field(
        description="Why this might be deus ex machina (no setup, no foreshadowing, etc.)"
    )
    setup_exists: bool = Field(description="Was this solution set up in prior chapters?")
    foreshadowing_ids: List[str] = Field(
        default_factory=list,
        description="Links to foreshadowing that justified this"
    )
    
    # For detection:
    # Query: "Find high-risk deus ex machina with setup_exists=False"


# ============================================================================
# Updated Core Model
# ============================================================================

class PlotExtraction(BaseModel):
    """All plot-related information from a chapter"""
    events: List[PlotEvent]
    causal_chains: List[CausalChain]
    plot_threads: List[PlotThread]
    story_questions: List[StoryQuestion]
    foreshadowing: List[ForeshadowingElement]
    callbacks: List[CallbackElement]
    deus_ex_machina_risks: List[DeusExMachinaRisk] = Field(
        default_factory=list,
        description="Potential contrived solutions"
    )


class ChapterPlotExtraction(BaseModel):
    """MongoDB document structure"""
    chapter_id: str
    story_id: str
    chapter_number: int
    events: List[PlotEvent]
    causal_chains: List[CausalChain]
    plot_threads: List[PlotThread]
    story_questions: List[StoryQuestion]
    foreshadowing: List[ForeshadowingElement]
    callbacks: List[CallbackElement]
    deus_ex_machina_risks: List[DeusExMachinaRisk] = Field(default_factory=list)