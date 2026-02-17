from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCommandCursor

from app.ai.models.character import Character
from app.schemas.character import ChapterEmotionalState, ChapterGoals, ChapterKnowledgeGained, CharacterArcResponse, CharacterResponse


class CharacterService:

    def __init__(self, mongodb: AsyncIOMotorDatabase):
        self.mongodb = mongodb


    async def get_all_characters(self, story_id: str, user_id: str) -> CharacterResponse:

        cursor: AsyncIOMotorCommandCursor = self.mongodb.character_extractions.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$unwind": "$characters"},
            {"$sort": {"chapter_number": -1}},
            {"$group": {
                "_id": "$characters.name",
                "character": {"$first": "$characters"}
            }}
        ])

        characters = [
            Character(**doc["character"]) async for doc in cursor
        ]

        return CharacterResponse(characters=characters)
    
    async def get_character_arc(
        self, 
        character_name: str, 
        story_id: str, 
        user_id: str
    ) -> CharacterArcResponse:

        cursor: AsyncIOMotorCommandCursor = self.mongodb.character_extractions.aggregate([
            {"$match": {"story_id": story_id, "user_id": user_id}},
            {"$unwind": "$characters"},
            {"$match": {"characters.name": character_name}},
            {"$sort": {"chapter_number": 1}},
            {"$group": {
                "_id": None,
                "emotional_states": {
                    "$push": {
                        "chapter_id": "$chapter_id",
                        "chapter_number": "$chapter_number",
                        "emotional_state": "$characters.emotional_state"
                    }
                },
                "goals": {
                    "$push": {
                        "chapter_id": "$chapter_id",
                        "chapter_number": "$chapter_number",
                        "goals": "$characters.goals"
                    }
                },
                "knowledge_gained": {
                    "$push": {
                        "chapter_id": "$chapter_id",
                        "chapter_number": "$chapter_number",
                        "knowledge_gained": "$characters.knowledge_gained"
                    }
                }
            }}
        ])

        character_arcs = await cursor.to_list(length=1)

        if not character_arcs:
            return CharacterArcResponse(character_name=character_name)
        
        character_arc = character_arcs[0]

        return CharacterArcResponse(
            character_name=character_name,
            emotional_states=[ChapterEmotionalState(**state) for state in character_arc["emotional_states"]],
            goals=[ChapterGoals(**chapter_goal) for chapter_goal in character_arc["goals"]],
            knowledge_gained=[ChapterKnowledgeGained(**chapter_knowledge) for chapter_knowledge in character_arc["knowledge_gained"]]
        )

