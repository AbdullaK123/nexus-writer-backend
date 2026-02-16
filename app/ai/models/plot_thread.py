from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class PlotThread(BaseModel):
    """A single plot thread/storyline"""
    
    thread_id: str = Field(description="Unique snake_case identifier for this thread, stable across analyses (e.g., 'main_conspiracy', 'chen_redemption_arc'). Must be deterministic — the same thread always gets the same ID.")
    name: str = Field(description="Human-readable short name for this plot thread (e.g., 'The Conspiracy', 'Chen's Redemption')")
    thread_type: Literal["main", "subplot", "character_arc", "mystery", "romance"] = Field(
        description="Category of this thread: 'main' (central story engine), 'subplot' (secondary storyline), 'character_arc' (personal growth/change), 'mystery' (unanswered question driving tension), 'romance' (relationship-focused)"
    )
    description: str = Field(description="A 1-2 sentence summary of what this thread is about and what drives it forward")
    
    status: Literal["active", "resolved", "abandoned", "dormant"] = Field(
        description="Current state: 'active' (progressing), 'resolved' (concluded satisfactorily), 'abandoned' (dropped without resolution), 'dormant' (inactive but not closed)"
    )
    introduced_chapter: int = Field(description="Chapter number where this thread was first introduced or became recognizable as a distinct storyline")
    resolved_chapter: Optional[int] = Field(default=None, description="Chapter number where this thread reached resolution, or None if still open")
    
    stakes: str = Field(description="What is at risk if this thread's conflict is not resolved — the consequences of failure (e.g., 'The colony will be destroyed if the artifact isn't neutralized')")
    goal: str = Field(description="The objective that would resolve this thread — what needs to happen for it to conclude (e.g., 'Expose the mole before they can transmit the colony's coordinates')")
    
    primary_characters: List[str] = Field(default=[], max_length=6, description="Canonical names of characters most central to this thread, ordered by involvement")
    key_chapters: List[int] = Field(default=[], max_length=15, description="Chapter numbers where this thread had major developments, turning points, or escalations")
    
    resolution_summary: Optional[str] = Field(default=None, description="How this thread was resolved, if applicable — 1-2 sentences covering the outcome and its consequences. None if unresolved.")


class StoryQuestion(BaseModel):
    """A question raised or answered by the narrative"""
    question: str = Field(description="The specific narrative question phrased as a reader would think it (e.g., 'Who killed the ambassador?' or 'Will Chen choose duty over family?')")
    raised_chapter: int = Field(description="Chapter number where this question was first posed or became apparent to the reader")
    answered_chapter: Optional[int] = Field(default=None, description="Chapter number where this question was definitively answered, or None if still open")
    answer: Optional[str] = Field(default=None, description="The answer provided by the narrative, if resolved (e.g., 'The ambassador faked his own death to escape the conspiracy')")
    importance: Literal["critical", "major", "minor"] = Field(
        description="Narrative weight: 'critical' (central mystery the story hinges on), 'major' (significant question affecting plot direction), 'minor' (small curiosity or subplot detail)"
    )


class PlotThreadWarning(BaseModel):
    """Potential issues with plot threads"""
    thread_id: str = Field(description="The thread_id of the affected plot thread, matching the PlotThread.thread_id value")
    warning_type: Literal["dormant", "rushed", "dangling", "contradictory"] = Field(
        description="Type of issue: 'dormant' (thread inactive for too long), 'rushed' (resolved too quickly without buildup), 'dangling' (introduced but never picked up again), 'contradictory' (thread details conflict with themselves)"
    )
    severity: Literal["minor", "moderate", "major"] = Field(
        description="Impact level: 'minor' (most readers won't notice), 'moderate' (attentive readers will spot it), 'major' (clearly broken and damages the narrative)"
    )
    description: str = Field(description="Specific explanation of the problem, citing relevant chapter numbers and details (e.g., 'The saboteur subplot was introduced in Ch. 4 but hasn't been mentioned in 8 chapters')")
    recommendation: str = Field(description="Actionable fix with chapter references (e.g., 'Add a brief reminder in Ch. 10 dialogue to keep the saboteur thread alive, then resolve in Ch. 14')")


class PlotThreadsExtraction(BaseModel):
    """Complete plot thread analysis for a story"""
    
    threads: List[PlotThread] = Field(max_length=20, description="Every distinct plot thread identified across the full story, including resolved and abandoned threads")
    
    total_threads: int = Field(description="Total number of distinct plot threads identified")
    active_thread_ids: List[str] = Field(default=[], max_length=15, description="thread_id values for threads with status 'active' — still in progress and unresolved")
    resolved_thread_ids: List[str] = Field(default=[], max_length=15, description="thread_id values for threads with status 'resolved' — concluded within the narrative")
    
    unanswered_questions: List[StoryQuestion] = Field(default=[], max_length=15, description="Narrative questions that have been raised but not yet answered as of the latest chapter")
    warnings: List[PlotThreadWarning] = Field(default=[], max_length=10, description="Detected structural issues with plot threads that may indicate problems for readers")
    
    plot_complexity_score: int = Field(ge=1, le=10, description="How many interwoven threads the story juggles: 1-3 = simple/focused, 4-6 = moderately complex, 7-9 = highly complex, 10 = extremely intricate with many interdependent threads")
    plot_coherence_score: int = Field(ge=1, le=10, description="How well the threads connect and support each other: 1-3 = fragmented/disconnected, 4-6 = mostly cohesive, 7-9 = tightly woven, 10 = masterfully integrated")
    
    narrative_summary: str = Field(description="A 2-4 sentence overview of the story's plot architecture — how the main thread and subplots interrelate, where they converge, and the overall narrative shape")
    
    generated_at: datetime = Field(default_factory=datetime.now)