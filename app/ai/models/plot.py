"""
Plot extraction models — optimized for detecting:
- Abandoned plot threads (importance + recency tracking)
- Chekhov's Gun violations (setup without payoff)
- Deus ex machina (solutions without prior setup)
- Unanswered story questions
"""
from typing import Literal
from pydantic import BaseModel, Field


class PlotEvent(BaseModel):
    """A significant event that happened in this chapter."""
    event: str = Field(description="What happened in 1-2 sentences")
    characters: list[str] = Field(description="Characters directly involved (canonical names)")
    location: str = Field(description="Where it happened")
    outcome: str = Field(description="Immediate result/consequence")


class PlotThread(BaseModel):
    """A storyline being tracked. Powers abandoned thread detection."""
    name: str = Field(description="Short name for this storyline")
    status: Literal["introduced", "active", "resolved", "dormant"] = Field(
        description="Current status this chapter"
    )
    importance: int = Field(ge=1, le=10, description="1=minor flavor, 10=central plot")
    must_resolve: bool = Field(description="True if this thread MUST have resolution by story end")


class Setup(BaseModel):
    """Foreshadowing or Chekhov's gun. Powers unfired-setup detection."""
    element: str = Field(description="What was set up: object, ability, detail, promise")
    emphasis: int = Field(ge=1, le=10, description="How strongly emphasized. High emphasis = MUST pay off")
    must_pay_off: bool = Field(description="True if this is a Chekhov's gun that must fire")


class Payoff(BaseModel):
    """Resolution of an earlier setup. Matched to Setup in post-processing."""
    element: str = Field(description="What was referenced/resolved from earlier chapters")
    resolution: Literal["full", "partial", "reminder"] = Field(
        description="How completely it was resolved"
    )


class StoryQuestion(BaseModel):
    """A mystery or tension question. Powers unanswered-question tracking."""
    question: str = Field(description="The question driving tension")
    status: Literal["raised", "answered"] = Field(
        description="Was it posed or resolved this chapter"
    )
    importance: int = Field(ge=1, le=10, description="1=minor curiosity, 10=central mystery")


class ContrivanceRisk(BaseModel):
    """Potential deus ex machina. Powers contrived-solution detection."""
    solution: str = Field(description="How the problem was solved")
    problem: str = Field(description="What problem it solved")
    risk: int = Field(ge=1, le=10, description="1=well set up, 10=completely out of nowhere")
    has_prior_setup: bool = Field(description="True if this solution was foreshadowed in earlier chapters")


class PlotExtraction(BaseModel):
    """All plot data extracted from a single chapter."""
    events: list[PlotEvent] = Field(default_factory=list)
    threads: list[PlotThread] = Field(default_factory=list)
    setups: list[Setup] = Field(default_factory=list)
    payoffs: list[Payoff] = Field(default_factory=list)
    questions: list[StoryQuestion] = Field(default_factory=list)
    contrivance_risks: list[ContrivanceRisk] = Field(default_factory=list)

    @classmethod
    def empty(cls) -> "PlotExtraction":
        """Return a valid empty extraction for use as a fallback."""
        return cls()
