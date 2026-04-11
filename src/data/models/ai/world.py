"""
World extraction model — laser focused on contradiction detection.
Facts are entity/attribute/value triples compared across chapters.
"""
from pydantic import BaseModel, Field


class Fact(BaseModel):
    """A concrete, verifiable STATE claim — NOT an action or event. Compared across chapters to detect contradictions."""
    entity: str = Field(description="The specific subject of this fact — a character name, location, object, species, or organization, using the canonical name (e.g., 'Commander Vex', 'Ironhold Station', 'the Beacon')")
    attribute: str = Field(description="A stable, reusable PROPERTY name in snake_case (e.g., 'eye_color', 'population', 'rank', 'weapon', 'location'). NEVER use 'action', 'dialogue', 'event', or 'status_update' — those are events, not continuity facts.")
    value: str = Field(description="The stated value including units where applicable — must be specific enough to detect contradictions (e.g., 'blue', '34 years old', '6 days by horse', 'left arm', '2,000 inhabitants')")


class WorldExtraction(BaseModel):
    """World/continuity data from a single chapter. Maximum 20 facts."""
    facts: list[Fact] = Field(
        default_factory=list,
        max_length=20,
        description="EXACTLY 10-20 fact triples. NEVER exceed 20. Each must be a STATIC STATE (who/what has what property) — not an action or event. Prioritize: physical traits, numbers/measurements, relationships, object ownership, ability rules, spatial relationships, injuries. Do NOT record what characters DID — only what IS TRUE about the world at chapter end. Every fact must be UNIQUE — no duplicate entity+attribute pairs."
    )

    @classmethod
    def empty(cls) -> "WorldExtraction":
        return cls()
