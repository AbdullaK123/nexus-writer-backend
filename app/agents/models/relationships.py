from pydantic import BaseModel, Field

class CharacterRelationship(BaseModel):
    """This is what the llm will extract from the chapter text."""
    source_name: str = Field(
        description="Name of the first character in the relationship."
    )
    target_name: str = Field(
        description="Name of the second character in the relationship."
    )
    relationship_type: str = Field(
        description="Nature of the relationship: 'ally', 'enemy', 'mentor', 'family', 'romantic', 'rival', or other descriptor.",
        max_length=50
    )
    description: str = Field(
        description="1-2 sentences describing the current dynamic between these characters in this chapter.",
        max_length=300
    )
    sentiment: str = Field(
        description="Overall tone: 'positive', 'negative', 'neutral', 'complicated'."
    )

    def to_edge(
        self,
        source_id: str,
        target_id: str,
        chapter_id: str
    ) -> "CharacterRelationshipEdge":
        return CharacterRelationshipEdge(
            source_id=source_id,
            target_id=target_id,
            chapter_id=chapter_id,
            **self.model_dump()
        )

class CharacterRelationshipEdge(CharacterRelationship):
    source_id: str = Field(
        description="The Entity ID of the first character in the relationship."
    )
    target_id: str = Field(
        description="The Entity ID of the second character in the relationship."
    )
    chapter_id: str = Field(
        description="ID of the chapter where this relationship state is observed."
    )