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
    event: str = Field(description="What happened in 1-2 sentences, focusing on the action and its immediate stakes (e.g., 'Vex discovers the signal is coming from inside the station, not the asteroid belt as assumed')")
    characters: list[str] = Field(max_length=8, description="Characters directly involved in or materially affected by this event (canonical full names). Exclude bystanders.")
    location: str = Field(description="The specific location where this event takes place, using the most precise name available (e.g., 'Bridge of the Artemis' not just 'the ship')")
    outcome: str = Field(description="The immediate consequence or result of this event that changes the story state (e.g., 'The crew is now trapped on Deck 7 with no comms')")


class PlotThread(BaseModel):
    """A storyline being tracked. Powers abandoned thread detection."""
    name: str = Field(description="A short, consistent label for this storyline used across all chapters (e.g., 'Vex mutiny subplot', 'Origin of the artifact'). Must match the same thread name used in other chapters for tracking.")
    status: Literal["introduced", "active", "resolved", "dormant"] = Field(
        description="This thread's status as of THIS chapter: 'introduced' (first mention), 'active' (progressed), 'resolved' (concluded), 'dormant' (present in earlier chapters but not advanced here)"
    )
    importance: int = Field(ge=1, le=10, description="Narrative weight: 1-3 = flavor/atmosphere detail, 4-6 = meaningful subplot, 7-9 = major storyline, 10 = THE central plot")
    must_resolve: bool = Field(description="True if this thread has been given enough narrative weight that leaving it unresolved would feel like a plot hole or broken promise to the reader")


class Setup(BaseModel):
    """Foreshadowing or Chekhov's gun. Powers unfired-setup detection."""
    element: str = Field(description="The specific thing that was set up or foreshadowed: a named object, revealed ability, emphasized detail, or narrative promise (e.g., 'The locked room on Deck 3 that the captain forbids anyone from entering')")
    emphasis: int = Field(ge=1, le=10, description="How strongly the narrative draws attention to this element: 1-3 = subtle background detail, 4-6 = mentioned deliberately, 7-9 = heavily emphasized, 10 = impossible to miss")
    must_pay_off: bool = Field(description="True if this setup is a clear Chekhov's gun — the narrative has placed enough emphasis that readers will expect it to matter later. False for atmospheric details or minor foreshadowing.")


class Payoff(BaseModel):
    """Resolution of an earlier setup. Matched to Setup in post-processing."""
    element: str = Field(description="The previously set-up element that is referenced or resolved here — use the same wording as the original Setup.element for accurate matching (e.g., 'The locked room on Deck 3')")
    resolution: Literal["full", "partial", "reminder"] = Field(
        description="How completely the setup was resolved: 'full' (completely paid off), 'partial' (addressed but not fully resolved), 'reminder' (referenced to keep it alive without resolving)"
    )


class StoryQuestion(BaseModel):
    """A mystery or tension question. Powers unanswered-question tracking."""
    question: str = Field(description="The specific narrative question that creates tension or curiosity for the reader, phrased as a question (e.g., 'Who sabotaged the oxygen recyclers?' or 'Will Vex betray the crew to save her sister?')")
    status: Literal["raised", "answered"] = Field(
        description="Whether this question was newly RAISED in this chapter or definitively ANSWERED. Only mark 'answered' if the text provides a clear resolution, not just a hint."
    )
    importance: int = Field(ge=1, le=10, description="Narrative weight of this question: 1-3 = minor curiosity or detail, 4-6 = significant subplot question, 7-9 = major story question, 10 = THE central mystery")


class ContrivanceRisk(BaseModel):
    """Potential deus ex machina. Powers contrived-solution detection."""
    solution: str = Field(description="The solution or resolution used in this chapter, described specifically (e.g., 'Chen suddenly reveals she can hack alien systems, a skill never mentioned before')")
    problem: str = Field(description="The problem or conflict that this solution addresses (e.g., 'The crew is locked out of the navigation computer by alien encryption')")
    risk: int = Field(ge=1, le=10, description="Contrivance level: 1-3 = well foreshadowed and earned, 4-6 = somewhat convenient but plausible, 7-9 = feels unearned or too convenient, 10 = completely out of nowhere with zero prior setup")
    has_prior_setup: bool = Field(description="True if this solution was foreshadowed, hinted at, or established in any earlier chapter. False if it appears for the first time exactly when needed.")


class PlotExtraction(BaseModel):
    """All plot data extracted from a single chapter."""
    events: list[PlotEvent] = Field(default_factory=list, max_length=8, description="3-8 SIGNIFICANT plot events in this chapter. Only events that change the story state — not every action a character takes.")
    threads: list[PlotThread] = Field(default_factory=list, max_length=10, description="All storylines active or referenced in this chapter. Reuse thread names from prior chapters for tracking.")
    setups: list[Setup] = Field(default_factory=list, max_length=5, description="0-5 foreshadowing or Chekhov's gun elements introduced in this chapter. Only genuinely distinct setups.")
    payoffs: list[Payoff] = Field(default_factory=list, max_length=5, description="Resolutions of setups from earlier chapters. Only include if a prior setup is actually addressed.")
    questions: list[StoryQuestion] = Field(default_factory=list, max_length=5, description="0-5 narrative questions raised or answered in this chapter. Only significant reader questions, not trivial details.")
    contrivance_risks: list[ContrivanceRisk] = Field(default_factory=list, max_length=3, description="0-3 potential deus ex machina situations. Only flag solutions that feel unearned or insufficiently foreshadowed.")

    @classmethod
    def empty(cls) -> "PlotExtraction":
        """Return a valid empty extraction for use as a fallback."""
        return cls()
