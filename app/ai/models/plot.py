"""
Plot extraction models — optimized for detecting:
- Abandoned plot threads (importance + recency tracking)
- Chekhov's Gun violations (setup without payoff)
- Deus ex machina (solutions without prior setup)
- Unanswered story questions

IMPORTANT: Several downstream services perform EXACT STRING MATCHING across
chapters to track plot elements. Thread names, setup elements, payoff elements,
and story question text MUST be character-for-character identical when referring
to the same narrative element across different chapters.
"""
from typing import Literal
from pydantic import BaseModel, Field


class PlotEvent(BaseModel):
    """A significant event that happened in this chapter."""
    event: str = Field(description="What happened in 1-2 sentences, focusing on the action and its immediate stakes (e.g., 'Vex discovers the signal is coming from inside the station, not the asteroid belt as assumed')")
    characters: list[str] = Field(default_factory=list, max_length=8, description="Characters directly involved in or materially affected by this event (canonical full names). Exclude bystanders.")
    location: str = Field(description="The specific location where this event takes place, using the most precise name available (e.g., 'Bridge of the Artemis' not just 'the ship')")
    outcome: str = Field(description="The immediate consequence or result of this event that changes the story state (e.g., 'The crew is now trapped on Deck 7 with no comms')")


class PlotThread(BaseModel):
    """A storyline being tracked. Powers abandoned thread detection."""
    name: str = Field(description="A short, fixed label for this storyline that MUST remain CHARACTER-FOR-CHARACTER IDENTICAL across every chapter it appears in. Once a thread is named 'Vex mutiny subplot', it must always be 'Vex mutiny subplot' — never 'The Vex mutiny', 'Vex's mutiny subplot', or any variation. Check the accumulated context for existing thread names and reuse them exactly. New threads should use lowercase with spaces (e.g., 'origin of the artifact', 'chen redemption arc').")
    status: Literal["introduced", "active", "resolved", "dormant"] = Field(
        description="This thread's status as of the END of this chapter: 'introduced' (first appearance in the story — use ONLY if this thread has ZERO mentions in accumulated context), 'active' (thread advanced or progressed this chapter), 'resolved' (thread reached a definitive conclusion this chapter — use ONLY when the storyline is fully closed), 'dormant' (thread exists from earlier chapters but was not advanced or mentioned this chapter)"
    )
    importance: int = Field(ge=1, le=10, description="Narrative weight: 1-3 = flavor/atmosphere detail, 4-6 = meaningful subplot, 7-9 = major storyline, 10 = THE central plot")
    must_resolve: bool = Field(description="True if this thread has been given enough narrative weight that leaving it unresolved would feel like a plot hole or broken promise to the reader. Once set to True for a thread, it should remain True in subsequent chapters unless the thread is resolved.")


class Setup(BaseModel):
    """Foreshadowing or Chekhov's gun. Powers unfired-setup detection."""
    element: str = Field(description="A fixed, reusable label for the thing that was set up — a named object, revealed ability, emphasized detail, or narrative promise. This label MUST be CHARACTER-FOR-CHARACTER IDENTICAL to any matching Payoff.element in later chapters. Use a short, specific, lowercase phrase (e.g., 'locked room on deck 3', 'chen alien language ability', 'the commander vex scar'). Do NOT use full sentences or varying descriptions.")
    emphasis: int = Field(ge=1, le=10, description="How strongly the narrative draws attention to this element: 1-3 = subtle background detail, 4-6 = mentioned deliberately, 7-9 = heavily emphasized, 10 = impossible to miss")
    must_pay_off: bool = Field(description="True if this setup is a clear Chekhov's gun — the narrative has placed enough emphasis that readers will expect it to matter later. False for atmospheric details or minor foreshadowing.")


class Payoff(BaseModel):
    """Resolution of an earlier setup. Matched to Setup by exact element string."""
    element: str = Field(description="The EXACT string used in the original Setup.element that this payoff resolves. Must be CHARACTER-FOR-CHARACTER IDENTICAL to the setup it references (e.g., if the setup was 'locked room on deck 3', this must be exactly 'locked room on deck 3' — not 'the locked room', 'Deck 3 room', or any variation). Check accumulated context for the exact setup labels used in prior chapters.")
    resolution: Literal["full", "partial", "reminder"] = Field(
        description="How completely the setup was resolved: 'full' (completely paid off — the narrative promise is fulfilled and this element needs no further attention), 'partial' (addressed but not fully resolved — the element was used but questions remain), 'reminder' (referenced to keep it alive in the reader's mind without resolving)"
    )


class StoryQuestion(BaseModel):
    """A mystery or tension question. Powers unanswered-question tracking."""
    question: str = Field(description="A fixed question string that MUST be CHARACTER-FOR-CHARACTER IDENTICAL when the same question appears across chapters. When a question is RAISED, write it as a short, specific reader question in lowercase (e.g., 'who sabotaged the oxygen recyclers?', 'will vex betray the crew to save her sister?'). When a question is ANSWERED in a later chapter, use the EXACT same string from when it was raised. Check accumulated context for previously raised questions and copy them verbatim.")
    status: Literal["raised", "answered"] = Field(
        description="Whether this question was newly RAISED in this chapter or definitively ANSWERED. Use 'raised' ONLY for questions appearing for the first time — if the question exists in accumulated context, do not re-raise it. Use 'answered' ONLY when the text provides a clear, definitive resolution — hints, partial reveals, and red herrings do NOT count as answered."
    )
    importance: int = Field(ge=1, le=10, description="Narrative weight of this question: 1-3 = minor curiosity or detail, 4-6 = significant subplot question, 7-9 = major story question, 10 = THE central mystery")


class ContrivanceRisk(BaseModel):
    """Potential deus ex machina. Powers contrived-solution detection."""
    solution: str = Field(description="The solution or resolution used in this chapter, described specifically (e.g., 'Chen suddenly reveals she can hack alien systems, a skill never mentioned before')")
    problem: str = Field(description="The problem or conflict that this solution addresses (e.g., 'The crew is locked out of the navigation computer by alien encryption')")
    risk: int = Field(ge=1, le=10, description="Contrivance level: 1-3 = well foreshadowed and earned, 4-6 = somewhat convenient but plausible, 7-9 = feels unearned or too convenient, 10 = completely out of nowhere with zero prior setup")
    has_prior_setup: bool = Field(description="True ONLY if this solution was explicitly foreshadowed, demonstrated, or established in a prior chapter visible in the accumulated context. False if the ability, tool, or knowledge appears for the first time in the same chapter it is needed. When in doubt, set to False — it is better to flag a potential contrivance than to miss one.")


# ── Per-component parser models ──────────────────────────────


class EventsExtraction(BaseModel):
    """Plot events extracted from analysis."""
    events: list[PlotEvent] = Field(default_factory=list, max_length=8, description="3-8 SIGNIFICANT plot events in this chapter. Only events that change the story state — not every action a character takes.")


class ThreadsExtraction(BaseModel):
    """Plot threads extracted from analysis."""
    threads: list[PlotThread] = Field(default_factory=list, max_length=10, description="All storylines active or referenced in this chapter. REUSE EXACT thread names from accumulated context. Only create new thread names for genuinely new storylines not present in prior chapters.")


class SetupsPayoffsExtraction(BaseModel):
    """Setups and payoffs extracted from analysis. Grouped together because payoffs reference setups by exact element string."""
    setups: list[Setup] = Field(default_factory=list, max_length=5, description="0-5 foreshadowing or Chekhov's gun elements INTRODUCED in this chapter. Use short, fixed, lowercase labels as element names. Do NOT duplicate setups already present in accumulated context — only new setups.")
    payoffs: list[Payoff] = Field(default_factory=list, max_length=5, description="Resolutions of setups from EARLIER chapters. The element field MUST exactly match a Setup.element from a prior chapter. Only include if a prior setup is actually addressed in this chapter's text.")


class QuestionsContrivancesExtraction(BaseModel):
    """Story questions and contrivance risks extracted from analysis."""
    questions: list[StoryQuestion] = Field(default_factory=list, max_length=5, description="0-5 narrative questions raised or answered in this chapter. Use short, fixed, lowercase question strings. When answering a prior question, copy the exact question string from accumulated context.")
    contrivance_risks: list[ContrivanceRisk] = Field(default_factory=list, max_length=3, description="0-3 potential deus ex machina situations. Only flag solutions that feel unearned or insufficiently foreshadowed. Check accumulated context thoroughly before setting has_prior_setup to True.")


# ── Composite model ─────────────────────────────────────────


class PlotExtraction(BaseModel):
    """All plot data extracted from a single chapter."""
    events: list[PlotEvent] = Field(default_factory=list, max_length=8, description="3-8 SIGNIFICANT plot events in this chapter. Only events that change the story state — not every action a character takes.")
    threads: list[PlotThread] = Field(default_factory=list, max_length=10, description="All storylines active or referenced in this chapter. REUSE EXACT thread names from accumulated context. Only create new thread names for genuinely new storylines not present in prior chapters.")
    setups: list[Setup] = Field(default_factory=list, max_length=5, description="0-5 foreshadowing or Chekhov's gun elements INTRODUCED in this chapter. Use short, fixed, lowercase labels as element names. Do NOT duplicate setups already present in accumulated context — only new setups.")
    payoffs: list[Payoff] = Field(default_factory=list, max_length=5, description="Resolutions of setups from EARLIER chapters. The element field MUST exactly match a Setup.element from a prior chapter. Only include if a prior setup is actually addressed in this chapter's text.")
    questions: list[StoryQuestion] = Field(default_factory=list, max_length=5, description="0-5 narrative questions raised or answered in this chapter. Use short, fixed, lowercase question strings. When answering a prior question, copy the exact question string from accumulated context.")
    contrivance_risks: list[ContrivanceRisk] = Field(default_factory=list, max_length=3, description="0-3 potential deus ex machina situations. Only flag solutions that feel unearned or insufficiently foreshadowed. Check accumulated context thoroughly before setting has_prior_setup to True.")

    @classmethod
    def from_components(
        cls,
        events: EventsExtraction,
        threads: ThreadsExtraction,
        setups_payoffs: SetupsPayoffsExtraction,
        questions_contrivances: QuestionsContrivancesExtraction,
    ) -> "PlotExtraction":
        """Synthesize from individual parser results."""
        return cls(
            events=events.events,
            threads=threads.threads,
            setups=setups_payoffs.setups,
            payoffs=setups_payoffs.payoffs,
            questions=questions_contrivances.questions,
            contrivance_risks=questions_contrivances.contrivance_risks,
        )

    @classmethod
    def empty(cls) -> "PlotExtraction":
        """Return a valid empty extraction for use as a fallback."""
        return cls()