from fastapi import Depends, HTTPException, status
from langchain.messages import HumanMessage, SystemMessage
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCommandCursor
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config.settings import app_config
from app.ai.prompts.character import CHARACTER_INCONSISTENCY_PROMPT
from app.ai.models.character import Character
from app.core.mongodb import get_mongodb
from app.schemas.character import ChapterEmotionalState, ChapterGoals, ChapterKnowledgeGained, CharacterArcResponse, CharacterInconsistencyResponse, CharacterKnowledgeResponse, CharacterResponse
from app.utils.ai import extract_text

class CharacterService:

    def __init__(self, mongodb: AsyncIOMotorDatabase):
        self.mongodb = mongodb
        self._model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            temperature=app_config.ai_temperature,
            max_tokens=app_config.ai_maxtokens,
            timeout=app_config.ai_sdk_timeout,
            max_retries=app_config.ai_sdk_retries,
        )

    def _build_inconsistency_prompt(
        self,
        arc: CharacterArcResponse
    ) -> str:

        emotional_states = "\n".join(
            f"  Chapter {s.chapter_number}: {s.emotional_state}"
            for s in arc.emotional_states
        ) or "  No emotional states extracted."

        goals = "\n".join(
            f"  Chapter {g.chapter_number}: {', '.join(g.goals)}"
            for g in arc.goals
        ) or "  No goals extracted."

        knowledge_gained = "\n".join(
            f"  Chapter {k.chapter_number}: {', '.join(k.knowledge_gained)}"
            for k in arc.knowledge_gained
        ) or "  No knowledge extracted."

        return f"""
        CHARACTER: {arc.character_name}

        EMOTIONAL STATES BY CHAPTER:
        {emotional_states}

        GOALS BY CHAPTER:
        {goals}

        KNOWLEDGE GAINED BY CHAPTER:
        {knowledge_gained}
        """


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

    async def get_knowledge_at_chapter(
        self,
        character_name: str,
        story_id: str,
        user_id: str,
        chapter_number: int
    ) -> CharacterKnowledgeResponse:

        cursor: AsyncIOMotorCommandCursor = self.mongodb.character_extractions.aggregate([
            {"$match": {
                "story_id": story_id,
                "user_id": user_id,
                "chapter_number": {"$lte": chapter_number}
            }},
            {"$unwind": "$characters"},
            {"$match": {"characters.name": character_name}},
            {"$group": {
                "_id": None,
                "all_knowledge": {"$push": "$characters.knowledge_gained"},
            }},
            {"$project": {
                "knowledge": {
                    "$reduce": {
                        "input": "$all_knowledge",
                        "initialValue": [],
                        "in": {"$concatArrays": ["$$value", "$$this"]}
                    }
                }
            }}
        ])

        docs = await cursor.to_list(length=1)

        if not docs:
            return CharacterKnowledgeResponse(
                character_name=character_name,
                chapter_number=chapter_number,
                knowledge=[]
            )

        return CharacterKnowledgeResponse(
            character_name=character_name,
            chapter_number=chapter_number,
            knowledge=docs[0]["knowledge"]
        )
    
    async def get_inconsistency_report(
        self,
        story_id: str,
        user_id: str,
        character_name: str
    ) -> CharacterInconsistencyResponse:
        
        arc = await self.get_character_arc(
            character_name,
            story_id,
            user_id
        )

        if not arc.emotional_states and not arc.goals and not arc.knowledge_gained:
            return CharacterInconsistencyResponse(character_name=character_name)
        
        response = await self._model.ainvoke([
            SystemMessage(content=CHARACTER_INCONSISTENCY_PROMPT),
            HumanMessage(content=self._build_inconsistency_prompt(arc))
        ])

        return CharacterInconsistencyResponse(
            character_name=character_name,
            report=extract_text(response)
        )
    

async def get_character_service(
    mongodb=Depends(get_mongodb)
) -> CharacterService:
    return CharacterService(mongodb=mongodb)