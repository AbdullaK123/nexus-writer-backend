"""
World extraction models — optimized for detecting:
- Contradictions (any entity+attribute that changes between chapters)
- World rule establishment and tracking
- Timeline markers for temporal analysis
"""
from pydantic import BaseModel, Field


class Fact(BaseModel):
    """Any concrete, verifiable claim about the story world.
    Compared across chapters to detect contradictions."""
    entity: str = Field(description="Who or what this fact is about: a character name, location, object, organization, species, etc.")
    attribute: str = Field(description="The specific aspect being stated. Use snake_case. Examples: 'eye_color', 'population', 'age', 'distance_to_capital', 'max_speed', 'injury', 'travel_time', 'healing_status'")
    value: str = Field(description="The stated value, including units or qualifiers. Examples: 'blue', '40000 people', '34 years old', '6 days by horse', 'broken left femur (severe)', 'fully healed'")


class Location(BaseModel):
    """A named location that appears in this chapter."""
    name: str = Field(description="Proper name of the place")
    type: str = Field(description="Category: planet, city, building, ship, room, region, forest, etc.")
    is_new: bool = Field(description="True only if this is the first mention in the entire story so far")


class WorldRule(BaseModel):
    """A rule about how the story world works, either explicitly stated or clearly demonstrated through events."""
    rule: str = Field(description="Clear, specific statement of the rule. Example: 'Teleportation requires line of sight to destination'")
    type: str = Field(description="Category: magic, technology, social, physics, biological, political, economic, etc.")


class TimelineMarker(BaseModel):
    """A temporal reference that anchors when something happens in the story.
    Extract ALL time references — explicit dates, relative markers, and time-of-day mentions."""
    event: str = Field(description="Brief description of what happens at this point in time. Example: 'Sarah arrives at the castle', 'The battle ends'")
    time_reference: str = Field(description="The temporal marker as stated or implied in the text. Use the story's own wording. Examples: 'Day 3', 'three weeks after the war', 'that evening', 'Year 2185', 'the following morning', 'simultaneously with the attack'")
    time_of_day: str | None = Field(default=None, description="Time of day if mentioned or clearly implied: morning, midday, afternoon, evening, night, dawn, dusk")
    sequence: int = Field(description="Order of occurrence within this chapter, starting at 1. Use to reconstruct the chapter's internal chronology.")


class WorldExtraction(BaseModel):
    """All world/continuity data extracted from a single chapter."""
    facts: list[Fact] = Field(default_factory=list, description="Every concrete, verifiable claim. Include physical descriptions, measurements, dates, ages, distances, injuries, travel details, abilities, and any specific detail that could contradict a different chapter.")
    locations: list[Location] = Field(default_factory=list, description="All named locations mentioned in this chapter.")
    rules: list[WorldRule] = Field(default_factory=list, description="World rules explicitly stated or clearly demonstrated. Only include rules that are explained or shown, not merely hinted at.")
    timeline: list[TimelineMarker] = Field(default_factory=list, description="All temporal references in this chapter. Extract every time marker, even minor ones like 'that night' or 'hours later'. These are critical for building the story timeline.")

    @classmethod
    def empty(cls) -> "WorldExtraction":
        """Return a valid empty extraction for use as a fallback."""
        return cls()
