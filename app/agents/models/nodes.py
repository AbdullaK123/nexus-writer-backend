from pydantic import BaseModel, Field
from uuid import uuid4
from typing import List

def generate_id():
    return str(uuid4())

class Attribute(BaseModel):
    category: str = Field(
        description="Type of attribute: 'physical', 'personality', 'skill', 'behavior', or 'other'."
    )
    value: str = Field(
        description="The specific attribute as a short phrase."
    )

class Character(BaseModel):
    """This is what the llm will extract from the chapter text."""
    name: str = Field(
        description="Character's full name as it appears in the text. Use the most complete version mentioned."
    )
    state: str = Field(
        description="2-3 sentence summary of what the character is doing, their goals, and emotional state in this chapter.",
        max_length=500
    )
    attributes: List[Attribute] = Field(
        description="Observable traits revealed in this chapter."
    )

    def to_node(self, chapter_id: str, entity_id: str) -> "CharacterNode":
        return CharacterNode(
            **self.model_dump(),
            chapter_id=chapter_id,
            entity_id=entity_id
        )

class CharacterEntity(BaseModel):
    entity_id: str = Field(default_factory=generate_id)
    canonical_name: str
    aliases: List[str] = Field(default_factory=list)

class CharacterNode(Character):
    """This is what neo4j nodes will be serialized as in python"""
    id: str = Field(default_factory=generate_id)
    entity_id: str = Field(description="Reference to the canonical character entity in the database.")
    chapter_id: str = Field(
        description="ID of the chapter where this character is observed."
    )

