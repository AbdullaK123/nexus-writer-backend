from enum import Enum

class EntityType(str, Enum):
    CHARACTER = "character"
    LOCATION = "location"
    ORGANIZATION = "organization"
    ARTIFACT = "artifact"
    TECHNOLOGY = "technology"
    SPECIES = "species"


class IssueType(str, Enum):
    FILTER_WORD = "filter_word"
    WEAK_VERB = "weak_verb"
    REPETITION = "repetition"
    SHOW_VS_TELL = "show_vs_tell"
    DIALOGUE_TAG = "dialogue_tag"
    SENTENCE_VARIETY = "sentence_variety"
    VOICE_INCONSISTENCY = "voice_inconsistency"
    CONTINUITY_ERROR = "continuity_error"
    PACING = "pacing"
    PURPLE_PROSE = "purple_prose"


class StructuralRole(str, Enum):
    EXPOSITION = "exposition"
    INCITING_INCIDENT = "inciting_incident"
    RISING_ACTION = "rising_action"
    CLIMAX = "climax"
    FALLING_ACTION = "falling_action"
    RESOLUTION = "resolution"
    TRANSITION = "transition"
    FLASHBACK = "flashback"


class SceneType(str, Enum):
    ACTION = "action"
    DIALOGUE = "dialogue"
    INTROSPECTION = "introspection"
    EXPOSITION = "exposition"
    TRANSITION = "transition"


class PlotThreadStatus(str, Enum):
    INTRODUCED = "introduced"
    ACTIVE = "active"
    ADVANCED = "advanced"
    RESOLVED = "resolved"
    DORMANT = "dormant"
    ABANDONED = "abandoned"


class EmotionalState(str, Enum):
    CALM = "calm"
    ANXIOUS = "anxious"
    ANGRY = "angry"
    FEARFUL = "fearful"
    JOYFUL = "joyful"
    SORROWFUL = "sorrowful"
    CONFLICTED = "conflicted"
    DETERMINED = "determined"
    DEFEATED = "defeated"
    HOPEFUL = "hopeful"