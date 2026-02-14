"""
World extraction models — optimized for detecting:
- Contradictions (any entity+attribute that changes between chapters)
- World rule violations (established rules broken without explanation)
- Timeline impossibilities (temporal logic errors)
- Impossible healing (injuries recovered too fast)
- Impossible travel (distances vs time vs method)
"""
from typing import Literal
from pydantic import BaseModel, Field


class Fact(BaseModel):
    """Any concrete, verifiable claim. THE core contradiction detector.
    Query: GROUP BY (entity, attribute) across chapters -> find value changes."""
    entity: str = Field(description="Who or what: character name, location, object, etc.")
    attribute: str = Field(description="Which aspect: 'eye_color', 'population', 'distance_to_X', 'age', etc.")
    value: str = Field(description="The stated value: 'blue', '40,000', '6 days travel', '34 years old'")


class Location(BaseModel):
    """A location mentioned in this chapter."""
    name: str = Field(description="Proper name of the place")
    type: str = Field(description="planet, city, building, ship, room, region, etc.")
    is_new: bool = Field(description="True only if first mention in the entire story")


class WorldRule(BaseModel):
    """How something works in this world. Powers rule-violation detection."""
    rule: str = Field(description="Clear statement of how it works")
    type: str = Field(description="magic, technology, social, physics, biological, political, etc.")


class RuleViolation(BaseModel):
    """An established world rule was broken this chapter."""
    rule: str = Field(description="The rule that was violated (as stated previously)")
    violation: str = Field(description="What happened that breaks the rule")
    severity: int = Field(ge=1, le=10, description="1=nitpick, 10=world-breaking contradiction")
    explained: bool = Field(description="True if an in-story justification exists")


class TimelineMarker(BaseModel):
    """A temporal reference. Used to construct story timeline in post-processing."""
    description: str = Field(description="The temporal reference: '3 days after the battle', 'that evening', 'Year 2185'")
    time_of_day: str | None = Field(default=None, description="morning, afternoon, evening, night, dawn, dusk if mentioned")


class InjuryRecord(BaseModel):
    """An injury sustained or active. Powers impossible-healing detection."""
    character: str = Field(description="Who was injured (canonical name)")
    injury: str = Field(description="Type and location: 'broken left femur', 'stab wound to shoulder'")
    severity: int = Field(ge=1, le=10, description="1=scratch, 10=life-threatening")
    expected_healing: str = Field(description="Realistic recovery time: 'hours', '2-3 days', '6-8 weeks'")
    affects: list[str] = Field(default_factory=list, description="Activities impaired: 'running', 'using right arm', 'combat'")


class TravelRecord(BaseModel):
    """Travel between locations. Powers impossible-travel detection."""
    characters: list[str] = Field(description="Who traveled (canonical names)")
    origin: str = Field(description="Starting location")
    destination: str = Field(description="Ending location")
    method: str = Field(description="How: walking, horse, ship, car, teleportation, etc.")
    time_taken: str = Field(description="How long it took: '3 days', 'overnight', '10 minutes'")
    issue: str | None = Field(default=None, description="Why implausible, or null if plausible")


class WorldExtraction(BaseModel):
    """All world/continuity data extracted from a single chapter."""
    facts: list[Fact] = Field(default_factory=list)
    locations: list[Location] = Field(default_factory=list)
    rules: list[WorldRule] = Field(default_factory=list)
    violations: list[RuleViolation] = Field(default_factory=list)
    timeline: list[TimelineMarker] = Field(default_factory=list)
    injuries: list[InjuryRecord] = Field(default_factory=list)
    travel: list[TravelRecord] = Field(default_factory=list)
