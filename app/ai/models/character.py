"""
Character extraction models — optimized for detecting:
- Plot holes (knowledge tracking)
- Contradictions (via unified Fact model in world.py)
- Flat arcs (emotional state + goal diffs across chapters)
- Voice drift (dialogue formality/pattern consistency)
- Show vs Tell (trait demonstration vs narration)
"""
from pydantic import BaseModel, Field


class Character(BaseModel):
    """One entry per character present in the chapter."""
    name: str = Field(description="Canonical full name")
    aliases: list[str] = Field(default_factory=list, description="Other names/titles used THIS chapter")
    is_new: bool = Field(description="True only if first appearance in the entire story")
    role: str = Field(description="Their function this chapter in 1 sentence")
    location: str = Field(description="Where they are at chapter end")
    condition: str = Field(description="Physical state: 'healthy', 'broken arm, exhausted', etc.")
    emotional_state: str = Field(description="Emotional state at chapter end in free text")
    goals: list[str] = Field(default_factory=list, description="What they are actively trying to achieve")


class KnowledgeGain(BaseModel):
    """Information a character learned THIS chapter. Powers plot hole detection."""
    character: str = Field(description="Who learned it (canonical name)")
    knowledge: str = Field(description="What they learned")
    source: str = Field(description="How: 'witnessed', 'told by [name]', 'overheard', 'deduced', 'read'")


class DialogueVoice(BaseModel):
    """One sample per speaking character. Powers voice drift detection."""
    character: str = Field(description="Who spoke (canonical name)")
    sample: str = Field(description="Representative dialogue quote from this chapter")
    formality: int = Field(ge=1, le=10, description="1=very casual/slangy, 10=very formal/archaic")
    patterns: list[str] = Field(default_factory=list, description="Speech patterns: 'military jargon', 'no contractions', 'asks questions', etc.")


class TraitEvidence(BaseModel):
    """Every trait claim — shown or told. Powers show-vs-tell detection."""
    character: str = Field(description="Who (canonical name)")
    trait: str = Field(description="The trait: 'brave', 'intelligent', 'kind', etc.")
    shown: bool = Field(description="True if DEMONSTRATED through action/dialogue. False if NARRATED by author/character.")
    evidence: str = Field(description="The action that shows it, or the narration that tells it")


class CharacterExtraction(BaseModel):
    """All character data extracted from a single chapter."""
    characters: list[Character] = Field(default_factory=list)
    knowledge_gains: list[KnowledgeGain] = Field(default_factory=list)
    dialogue_voices: list[DialogueVoice] = Field(default_factory=list)
    trait_evidence: list[TraitEvidence] = Field(default_factory=list)

    @classmethod
    def empty(cls) -> "CharacterExtraction":
        """Return a valid empty extraction for use as a fallback."""
        return cls()
