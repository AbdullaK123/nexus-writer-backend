from typing import List, Optional, Dict, Literal
from pydantic import BaseModel, Field
from app.ai.models.enums import EmotionalState


# ============================================================================
# OPTIMIZED FOR: Character Continuity Detection
# ============================================================================

class PhysicalAppearance(BaseModel):
    """Structured physical description - enables continuity checking"""
    eye_color: Optional[str] = Field(None, description="Exact eye color if mentioned")
    hair_color: Optional[str] = Field(None, description="Hair color if mentioned")
    hair_style: Optional[str] = Field(None, description="Hair style/length if mentioned")
    height: Optional[str] = Field(None, description="Height description if mentioned")
    build: Optional[str] = Field(None, description="Body type if mentioned")
    skin_tone: Optional[str] = Field(None, description="Skin color/tone if mentioned")
    age_appearance: Optional[str] = Field(None, description="Apparent age if mentioned")
    distinguishing_marks: List[str] = Field(
        default_factory=list,
        description="Scars, tattoos, birthmarks, etc."
    )
    clothing_style: Optional[str] = Field(None, description="Typical attire if notable")
    
    # For detecting inconsistencies:
    # Can query: "Find characters where eye_color changed between chapters"


# ============================================================================
# OPTIMIZED FOR: Character Arc Tracking
# ============================================================================

class PersonalityTraits(BaseModel):
    """Quantified personality traits - enables arc analysis"""
    # Key: trait name, Value: 1-10 scale
    # Examples: "confident": 3, "empathetic": 9, "impulsive": 7
    traits: Dict[str, int] = Field(
        default_factory=dict,
        description="Personality traits rated 1-10. ONLY include traits explicitly shown in chapter."
    )
    
    # For detecting flat arcs:
    # Query: "Compare first chapter traits to last chapter, flag if change < 15%"


class CoreBelief(BaseModel):
    """Character's core belief - tracks belief changes over arc"""
    belief: str = Field(description="What they believe (e.g., 'family is everything')")
    strength: int = Field(ge=1, le=10, description="How strongly held (1=weak, 10=unshakeable)")
    challenged_this_chapter: bool = Field(
        default=False,
        description="Was this belief tested/questioned this chapter?"
    )
    
    # For detecting arcs:
    # Query: "Find beliefs that never get challenged" or "Find sudden belief changes"


class Relationship(BaseModel):
    """Relationship between two characters - tracks dynamics"""
    other_character: str = Field(description="The other character's name")
    relationship_type: str = Field(
        description="ally, enemy, romantic, mentor, rival, family, etc."
    )
    trust_level: int = Field(ge=1, le=10, description="How much they trust each other")
    current_status: str = Field(
        description="Current state: 'strong', 'strained', 'improving', 'deteriorating'"
    )
    dynamic_notes: Optional[str] = Field(None, description="Notable interactions this chapter")


# ============================================================================
# OPTIMIZED FOR: Plot Hole Detection (Knowledge Tracking)
# ============================================================================

class KnowledgeItem(BaseModel):
    """What a character knows - critical for plot hole detection"""
    fact_id: str = Field(description="Unique ID for this piece of information")
    knowledge: str = Field(description="What they know (e.g., 'the killer is left-handed')")
    learned_in_chapter: int = Field(description="Chapter where they learned this")
    source: str = Field(
        description="How they learned it: 'witnessed', 'overheard', 'told by [name]', 'deduced', 'assumed'"
    )
    certainty: Literal["certain", "suspected", "rumor"] = Field(
        default="certain",
        description="How certain is this knowledge"
    )
    
    # For plot hole detection:
    # Query: "Character references fact_id X but learned it AFTER current chapter"


class Skill(BaseModel):
    """Character skill or ability - tracks capability consistency"""
    skill_name: str = Field(description="e.g., 'sword fighting', 'medicine', 'persuasion'")
    proficiency: int = Field(ge=1, le=10, description="Skill level 1-10")
    demonstrated: bool = Field(
        description="Did they actually USE this skill, or was it just mentioned?"
    )
    first_revealed_chapter: Optional[int] = Field(
        None,
        description="When was this skill first shown/mentioned?"
    )
    
    # For Show vs Tell detection:
    # Query: "Skills mentioned but never demonstrated"


# ============================================================================
# OPTIMIZED FOR: Dialogue Voice Consistency
# ============================================================================

class DialogueSample(BaseModel):
    """Structured dialogue analysis - enables voice consistency checking"""
    character_name: str
    dialogue_text: str = Field(description="The actual dialogue spoken")
    formality_level: int = Field(
        ge=1, le=10,
        description="1=very casual/slangy, 10=very formal/archaic"
    )
    sentence_complexity: int = Field(
        ge=1, le=10,
        description="1=simple/short sentences, 10=complex/long sentences"
    )
    speech_patterns: List[str] = Field(
        default_factory=list,
        description="Notable patterns: 'uses contractions', 'no contractions', 'asks questions', 'uses metaphors'"
    )
    verbal_tics: List[str] = Field(
        default_factory=list,
        description="Repeated phrases or sounds: 'ya know', 'well...', 'hmm'"
    )
    emotional_tone: str = Field(description="angry, calm, excited, hesitant, etc.")
    vocabulary_level: int = Field(
        ge=1, le=10,
        description="1=simple words, 10=sophisticated vocabulary"
    )
    
    # For voice consistency:
    # Query: "Compare formality_level variance for same character across chapters"


# ============================================================================
# OPTIMIZED FOR: Show vs Tell Detection
# ============================================================================

class TraitClaim(BaseModel):
    """Claim about character trait - matches claims to demonstrations"""
    character_name: str
    trait: str = Field(description="The trait being claimed: 'brave', 'intelligent', 'kind'")
    claim_type: Literal["narrator_tells", "self_describes", "other_describes", "demonstrated"] = Field(
        description="How the trait was presented"
    )
    evidence: Optional[str] = Field(
        None,
        description="For 'demonstrated': the action that shows it. For others: the quote/description"
    )
    
    # For Show vs Tell:
    # Query: "Find traits with many 'narrator_tells' but zero 'demonstrated'"


# ============================================================================
# Updated Core Models
# ============================================================================

class CharacterMention(BaseModel):
    """A character mentioned in this chapter"""
    canonical_name: str = Field(description="Full name (e.g., 'Captain Sarah Chen')")
    aliases_used: List[str] = Field(default_factory=list, description="Names/titles used this chapter")
    is_new_character: bool = Field(description="First appearance in story?")
    role_in_chapter: str = Field(description="Their role/function this chapter")


class CharacterAction(BaseModel):
    """Significant action taken by a character - with motivation tracking"""
    character_name: str
    action: str = Field(description="What they did")
    motivation: Optional[str] = Field(
        None,
        description="WHY they did it (if clear from context)"
    )
    required_knowledge: List[str] = Field(
        default_factory=list,
        description="What they needed to know to take this action (for plot hole detection)"
    )
    required_skills: List[str] = Field(
        default_factory=list,
        description="What skills/abilities were needed (for continuity)"
    )
    consequence: Optional[str] = Field(None, description="Immediate result")
    

class CharacterSnapshot(BaseModel):
    """Complete state of a character at end of chapter - COMPREHENSIVE"""
    character_name: str
    
    # Physical & Location
    physical_appearance: Optional[PhysicalAppearance] = Field(
        None,
        description="Physical appearance details (only if mentioned this chapter)"
    )
    location: str
    
    # Psychological State
    emotional_state: List[EmotionalState] = Field(
        default_factory=list,
        description="Current emotions"
    )
    personality_traits: PersonalityTraits = Field(default_factory=PersonalityTraits)
    core_beliefs: List[CoreBelief] = Field(
        default_factory=list,
        description="Their fundamental beliefs"
    )
    
    # Capabilities
    skills_abilities: List[Skill] = Field(
        default_factory=list,
        description="Known skills and abilities"
    )
    physical_condition: str = Field(
        default="healthy",
        description="Injuries, illness, fatigue level"
    )
    
    # Story State
    goals: List[str] = Field(
        default_factory=list,
        description="What they're trying to achieve"
    )
    knowledge_state: List[KnowledgeItem] = Field(
        default_factory=list,
        description="What they know (for plot hole detection)"
    )
    relationships: List[Relationship] = Field(
        default_factory=list,
        description="Relationships with other characters"
    )
    internal_conflicts: List[str] = Field(
        default_factory=list,
        description="Internal struggles/dilemmas"
    )


class CharacterExtraction(BaseModel):
    """All character-related information from a chapter"""
    characters_present: List[CharacterMention]
    character_actions: List[CharacterAction]
    character_snapshots: List[CharacterSnapshot]
    dialogue_samples: List[DialogueSample] = Field(
        default_factory=list,
        description="Structured dialogue for voice analysis"
    )
    trait_claims: List[TraitClaim] = Field(
        default_factory=list,
        description="All trait claims (for show vs tell detection)"
    )


class ChapterCharacterExtraction(BaseModel):
    """MongoDB document structure"""
    chapter_id: str
    story_id: str
    chapter_number: int
    characters_present: List[CharacterMention]
    character_actions: List[CharacterAction]
    character_snapshots: List[CharacterSnapshot]
    dialogue_samples: List[DialogueSample] = Field(default_factory=list)
    trait_claims: List[TraitClaim] = Field(default_factory=list)