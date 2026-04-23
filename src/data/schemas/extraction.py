from pydantic import BaseModel, Field
from enum import Enum, StrEnum
from typing import List, Optional

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
    status: ThreadStatus = Field(
        description=(
            "Current state of the thread in the manuscript so far:\n"
            "- open: introduced and still unresolved; the reader is waiting on it\n"
            "- resolved: paid off, answered, or concluded on the page\n"
            "- dangling: introduced but seemingly forgotten or abandoned (a continuity flag for the writer)"
        ),
    )
    importance: ThreadImportance = Field(
        description=(
            "How structurally important this thread is to the story:\n"
            "- central: a main spine of the narrative\n"
            "- supporting: a notable subplot that meaningfully shapes the story\n"
            "- minor: a small or local thread (a single-scene mystery, brief tension, etc.)"
        ),
    )
    tags: List[str] = Field(
        description="2-5 short keywords (entity names preferred) the writer can use to locate this thread in the manuscript."
    )


class PlotThreadLedger(BaseModel):
    threads: List[PlotThread] = Field(
        description="The complete set of plot threads tracked across the story so far."
    )


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

class CharacterArcType(str, Enum):
    GROWTH = "growth"             # becomes wiser/stronger/more whole (positive change)
    FALL = "fall"                 # declines morally, mentally, or in fortune (tragic)
    REDEMPTION = "redemption"     # rises from a low/corrupt starting point
    CORRUPTION = "corruption"     # starts good, succumbs to darker influences
    DISILLUSIONMENT = "disillusionment"  # loses naive belief, sees the world as it is
    FLAT = "flat"                 # does not change; their constancy drives others' change
    UNKNOWN = "unknown"           # arc not yet discernible


class Character(BaseModel):
    name: str = Field(
        description="Character's primary name as used in the manuscript (verbatim). Use the most-commonly-used form across the story."
    )
    aliases: List[str] = Field(
        default_factory=list,
        description="Other names, titles, or epithets used for this character in the text. Best-effort — only include aliases that appear in the source summaries.",
    )
    importance: CharacterImportance = Field(
        description=(
            "How central this character is to the story:\n"
            "- protagonist: the lead viewpoint or driving figure (typically very few)\n"
            "- major: significant POV, antagonist, or co-lead whose arc shapes the plot\n"
            "- supporting: recurring character with meaningful presence but not driving the plot\n"
            "- minor: appears briefly or in a limited role"
        ),
    )
    status: CharacterStatus = Field(
        description=(
            "Where the character stands as of the latest summarized chapter:\n"
            "- active: present in the narrative or expected to return\n"
            "- departed: alive but written out of the current storyline\n"
            "- deceased: confirmed dead on the page\n"
            "- unknown: fate unclear or not yet established"
        ),
    )
    description: str = Field(
        description="2-4 sentence description capturing who this character is — role in the story, defining traits, what readers need to remember. Written from the reader's perspective, objective tone, present tense."
    )
    key_relationships: List[str] = Field(
        default_factory=list,
        description="Short phrases naming significant relationships. Example: 'Saedaris — ally turned reluctant partner'. Include only relationships that matter to the story.",
    )
    tags: List[str] = Field(
        description="2-5 short keywords (names, places, affiliations) the writer can use to locate this character's scenes in the manuscript."
    )
    arc: Optional[str] = Field(
        default=None,
        description=(
            "The character's narrative trajectory across the story so far — how they "
            "have changed, what they have learned, lost, or become. Describes "
            "transformation and development rather than static traits. Should reference "
            "the starting state, key turning points, and current state when known. "
            "Leave null if the character has not undergone meaningful change or there "
            "is insufficient material to assess one (e.g. minor characters, very early "
            "in the story)."
        ),
    )
    arc_type: Optional[CharacterArcType] = Field(
        default=None,
        description=(
            "The shape of the character's developmental trajectory. Choose the single "
            "best fit:\n"
            "- growth: becomes wiser, stronger, or more whole over time\n"
            "- fall: declines morally, mentally, or in circumstance (tragic arc)\n"
            "- redemption: rises from a flawed or corrupt starting point\n"
            "- corruption: starts good or innocent, succumbs to darker forces\n"
            "- disillusionment: loses idealism or naive belief; sees the world as it is\n"
            "- flat: does not meaningfully change; their constancy may drive others\n"
            "- unknown: arc cannot yet be determined from the available material\n"
            "Use 'unknown' rather than guessing for minor characters or early-story figures."
        ),
    )


class CharacterRoster(BaseModel):
    characters: List[Character] = Field(
        description="The complete cast of characters established in the story so far."
    )


# =================== WORLD EXTRACTION SCHEMAS ===========================


class EntityImportance(StrEnum):
    CENTRAL = "central"  # Frequently referenced, core to the setting
    SUPPORTING = "supporting"  # Notable recurring element
    MINOR = "minor"  # Mentioned but peripheral


_ENTITY_IMPORTANCE_DESC = (
    "How prominent this element is in the world of the story:\n"
    "- central: frequently referenced, core to the setting\n"
    "- supporting: a notable recurring element\n"
    "- minor: mentioned but peripheral"
)


class Place(BaseModel):
    name: str = Field(
        description="The place's name as used in the manuscript (verbatim)."
    )
    description: str = Field(
        description="2-4 sentence description. What is this place, where is it, what's distinctive about it, and why does it matter in the story."
    )
    importance: EntityImportance = Field(description=_ENTITY_IMPORTANCE_DESC)
    tags: List[str] = Field(
        description="2-5 keywords (affiliated factions, character names, nearby places) the writer can use to locate scenes set here."
    )


class Faction(BaseModel):
    name: str = Field(
        description="The faction's name as used in the manuscript (verbatim) — guild, order, kingdom, corporation, cult, etc."
    )
    description: str = Field(
        description="2-4 sentence description. Who they are, what they want, how they operate, their status in the story."
    )
    importance: EntityImportance = Field(description=_ENTITY_IMPORTANCE_DESC)
    tags: List[str] = Field(
        description="2-5 keywords (affiliated characters, rival factions, key locations) the writer can use to locate scenes involving this faction."
    )


class TechnologyOrSystem(BaseModel):
    name: str = Field(
        description="Short label for the technology, magic system, or other rule-based system as named in the text."
    )
    description: str = Field(
        description="2-4 sentence description. What this technology or system is, how it functions in the world, and any rules, costs, or limitations that govern its use (e.g. magic system constraints, energy sources, side effects, who can wield it)."
    )
    importance: EntityImportance = Field(description=_ENTITY_IMPORTANCE_DESC)
    tags: List[str] = Field(
        description="2-5 keywords (associated characters, factions, places, related systems) the writer can use to locate scenes where this is in play."
    )


class CulturalFact(BaseModel):
    name: str = Field(
        description="Short label for the custom, practice, social structure, language, or cultural element."
    )
    description: str = Field(
        description="2-4 sentence description of the cultural fact as established in the text."
    )
    importance: EntityImportance = Field(description=_ENTITY_IMPORTANCE_DESC)
    tags: List[str] = Field(
        description="2-5 keywords (associated factions, places, characters) the writer can use to locate scenes where this cultural element appears."
    )


class HistoricalEvent(BaseModel):
    name: str = Field(
        description="Short label for the historical event as referenced in the text."
    )
    description: str = Field(
        description="2-4 sentence description of the event and its significance to the present-day narrative."
    )
    importance: EntityImportance = Field(description=_ENTITY_IMPORTANCE_DESC)
    tags: List[str] = Field(
        description="2-5 keywords (involved factions, characters, places) the writer can use to trace references to this event."
    )


class OtherWorldFact(BaseModel):
    name: str = Field(
        description="Short label for a worldbuilding fact that does not fit the other categories (e.g. fauna, flora, cosmology, economy, calendar, climate)."
    )
    description: str = Field(
        description="2-4 sentence description of the fact as established in the text and why it matters to the story."
    )
    importance: EntityImportance = Field(description=_ENTITY_IMPORTANCE_DESC)
    tags: List[str] = Field(
        description="2-5 keywords (associated places, factions, characters, systems) the writer can use to locate references to this fact."
    )


type Entity = Place | Faction | TechnologyOrSystem | HistoricalEvent | OtherWorldFact | CulturalFact

class WorldBible(BaseModel):
    places: List[Place] = Field(
        default_factory=list,
        description="Locations established in the story — cities, regions, buildings, landscapes, realms.",
    )
    factions: List[Faction] = Field(
        default_factory=list,
        description="Organized groups — kingdoms, guilds, orders, corporations, cults, political bodies.",
    )
    technologies: List[TechnologyOrSystem] = Field(
        default_factory=list,
        description="Technologies, magic systems, and other rule-based systems that govern how things work in the world.",
    )
    cultural_facts: List[CulturalFact] = Field(
        default_factory=list,
        description="Customs, practices, social structures, languages, and other cultural elements established in the text.",
    )
    historical_events: List[HistoricalEvent] = Field(
        default_factory=list,
        description="Past events referenced in the text whose echoes still shape the present-day narrative.",
    )
    other: List[OtherWorldFact] = Field(
        default_factory=list,
        description="Worldbuilding facts that don't fit the other buckets — fauna, flora, cosmology, economy, calendar, climate, etc.",
    )


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
        description="Distinctive stylistic features that recur across the book — heavy dialogue, minimal dialogue tags, sensory density, epistolary fragments, in-world documents quoted, etc. Only include features consistently present or deliberately recurring.",
    )
