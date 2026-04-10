from fastapi import Depends
from langchain.messages import HumanMessage, SystemMessage
from src.infrastructure.config import config
from src.service.ai.utils.model_factory import create_chat_model
from src.service.ai.prompts.character import CHARACTER_INCONSISTENCY_PROMPT
from src.service.ai.models.character import Character
from src.infrastructure.db.mongodb import get_mongodb
from src.data.schemas.character import ChapterEmotionalState, ChapterGoals, ChapterKnowledgeGained, CharacterArcResponse, CharacterInconsistencyResponse, CharacterKnowledgeResponse, CharacterResponse
from src.service.ai.utils.ai import extract_text
from src.infrastructure.utils.retry import retry_llm
from src.data.repositories.mongo.character_extraction import CharacterExtractionRepo

class CharacterService:

    def __init__(self, repo: CharacterExtractionRepo):
        self.repo = repo
        self._model = create_chat_model(config.ai.lite_model)

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
        rows = await self.repo.get_latest_per_character(story_id, user_id)
        characters = [Character(**doc["character"]) for doc in rows]
        return CharacterResponse(characters=characters)
    
    async def get_character_arc(
        self, 
        character_name: str, 
        story_id: str, 
        user_id: str
    ) -> CharacterArcResponse:
        character_arcs = await self.repo.get_character_arc(story_id, user_id, character_name)

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
        docs = await self.repo.get_cumulative_knowledge(story_id, user_id, character_name, chapter_number)

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
    
    @retry_llm
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
    return CharacterService(repo=CharacterExtractionRepo(mongodb))
