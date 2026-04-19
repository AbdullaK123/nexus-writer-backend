from pydantic import BaseModel, Field
from enum import Enum
from typing import List

# =================== PLOT EXTRACTION SCHEMAS ===========================

class ThreadStatus(str, Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    DANGLING = "dangling"


class ThreadImportance(str, Enum):
    CENTRAL = "central"
    SUPPORTING = "supporting"
    MINOR = "minor"


class PlotThread(BaseModel):
    description: str = Field(
        description="One-sentence description of the narrative promise or question, phrased from the reader's perspective."
    )
    status: ThreadStatus
    importance: ThreadImportance
    tags: List[str] = Field(
        description="2-5 short keywords (entity names preferred) the writer can use to locate this thread in the manuscript."
    )


class PlotThreadLedger(BaseModel):
    threads: List[PlotThread]

# =================== CHARACTER EXTRACTION SCHEMAS ===========================


class CharacterImportance(str, Enum):
    PROTAGONIST = "protagonist"
    MAJOR = "major"
    SUPPORTING = "supporting"
    MINOR = "minor"


class CharacterStatus(str, Enum):
    ACTIVE = "active"
    DEPARTED = "departed"
    DECEASED = "deceased"
    UNKNOWN = "unknown"


class Character(BaseModel):
    name: str = Field(
        description="Character's primary name as used in the manuscript (verbatim). Use the most-commonly-used form across the story."
    )
    aliases: List[str] = Field(
        default_factory=list,
        description="Other names, titles, or epithets used for this character in the text. Best-effort — only include aliases that appear in the source summaries."
    )
    importance: CharacterImportance
    status: CharacterStatus
    description: str = Field(
        description="2-4 sentence description capturing who this character is — role in the story, defining traits, what readers need to remember. Written from the reader's perspective, objective tone, present tense."
    )
    key_relationships: List[str] = Field(
        default_factory=list,
        description="Short phrases naming significant relationships. Example: 'Saedaris — ally turned reluctant partner'. Include only relationships that matter to the story."
    )
    tags: List[str] = Field(
        description="2-5 short keywords (names, places, affiliations) the writer can use to locate this character's scenes in the manuscript."
    )


class CharacterRoster(BaseModel):
    characters: List[Character]

# =================== WORLD EXTRACTION SCHEMAS ===========================

from pydantic import BaseModel, Field
from enum import Enum


class EntityImportance(str, Enum):
    CENTRAL = "central"      # Frequently referenced, core to the setting
    SUPPORTING = "supporting"  # Notable recurring element
    MINOR = "minor"           # Mentioned but peripheral


class Place(BaseModel):
    name: str
    description: str = Field(
        description="2-4 sentence description. What is this place, where is it, what's distinctive about it, and why does it matter in the story."
    )
    importance: EntityImportance
    tags: List[str] = Field(
        description="2-5 keywords (affiliated factions, character names, nearby places) the writer can use to locate scenes set here."
    )


class Faction(BaseModel):
    name: str
    nature: str = Field(
        description="Short phrase naming what kind of entity this is — government, religious order, criminal network, corporation, military, etc."
    )
    description: str = Field(
        description="2-4 sentence description. Who they are, what they want, how they operate, their status in the story."
    )
    importance: EntityImportance
    tags: List[str]


class TechnologyOrSystem(BaseModel):
    name: str
    description: str = Field(
        description="2-4 sentence description. What this technology or system is and how it functions in the world."
    )
    rules: List[str] = Field(
        description="The specific rules, constraints, and limits the narrative has established about how this works. Capture these verbatim or near-verbatim from the source. These are what the writer has committed to and must stay consistent with."
    )
    importance: EntityImportance
    tags: List[str]


class CulturalFact(BaseModel):
    name: str = Field(
        description="Short label for the custom, practice, social structure, language, or cultural element."
    )
    description: str = Field(
        description="2-4 sentence description of the cultural fact as established in the text."
    )
    tags: List[str]


class HistoricalEvent(BaseModel):
    name: str = Field(
        description="Short label for the historical event as referenced in the text."
    )
    description: str = Field(
        description="2-4 sentence description of the event and its significance to the present-day narrative."
    )
    tags: List[str]


class OtherWorldFact(BaseModel):
    name: str
    description: str
    tags: List[str]


class WorldBible(BaseModel):
    places: List[Place] = Field(default_factory=list)
    factions: List[Faction] = Field(default_factory=list)
    technologies: List[TechnologyOrSystem] = Field(default_factory=list)
    cultural_facts: List[CulturalFact] = Field(default_factory=list)
    historical_events: List[HistoricalEvent] = Field(default_factory=list)
    other: List[OtherWorldFact] = Field(default_factory=list)


# ===================  STYLE EXTRACTION SCHEMAS ===========================

class ChapterPacing(str, Enum):
    BREAKNECK = "breakneck"
    FAST = "fast"
    STEADY = "steady"
    SLOW = "slow"
    MEDITATIVE = "meditative"


class VoiceProfile(BaseModel):
    pacing: List[ChapterPacing] = Field(
        description="Pacing descriptor for each chapter in order, one entry per chapter."
    )
    tone: List[List[str]] = Field(
        description="Tone descriptors for each chapter in order, one list per chapter. Each descriptor is a single lowercase word (e.g., 'grimdark', 'melancholic', 'whimsical', 'triumphant'). Multiple tones per chapter allowed when the chapter is tonally blended. Capture only dominant tones."
    )
    rhythm: str = Field(
        description="Sentence-level rhythm across the book. E.g., 'Short declarative sentences in action, long flowing prose in reflection' or 'Uniformly long, layered sentences'."
    )
    signature_features: List[str] = Field(
        default_factory=list,
        description="Distinctive stylistic features that recur across the book — heavy dialogue, minimal dialogue tags, sensory density, epistolary fragments, in-world documents quoted, etc. Only include features consistently present or deliberately recurring."
    )