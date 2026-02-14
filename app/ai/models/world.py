"""
World extraction model — laser focused on contradiction detection.
Facts are entity/attribute/value triples compared across chapters.
"""
from pydantic import BaseModel, Field


class Fact(BaseModel):
    """A concrete, verifiable claim. Compared across chapters to detect contradictions."""
    entity: str = Field(description="Who/what: character name, location, object, etc.")
    attribute: str = Field(description="What aspect, in snake_case: eye_color, age, distance_to_capital")
    value: str = Field(description="Stated value with units: 'blue', '34', '6 days by horse'")


class WorldExtraction(BaseModel):
    """World/continuity data from a single chapter."""
    facts: list[Fact] = Field(
        default_factory=list,
        description="10-20 verifiable claims most likely to contradict another chapter. Prioritize numbers, measurements, physical traits, relationships, injuries."
    )

    @classmethod
    def empty(cls) -> "WorldExtraction":
        return cls()
