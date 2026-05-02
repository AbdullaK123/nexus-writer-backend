import asyncpg
from typing import Any, List, Literal, Optional
from uuid_extensions import uuid7str
import json
from src.data.schemas.chat import ChatMessageRow, ChatThreadRow, ChatToolCallRow

Executor = Any

class ChatRepository:

    def __init__(
        self,
        pool: asyncpg.Pool
    ) -> None:
        self._pool = pool

    @property
    def pool(self) -> asyncpg.Pool:
        return self._pool
    
    def _exe(self, executor: Executor) -> Executor:
        return executor if executor is not None else self._pool
    

    async def create_thread(
        self, 
        user_id: str, 
        story_id: str,
        title: str,
        executor: Executor | None = None
    ) -> ChatThreadRow:
        sql = """
        INSERT INTO "chat_thread" (id, user_id, story_id, title)
        VALUES ($1, $2, $3, $4)
        RETURNING *
        """
        row = await self._exe(executor).fetchrow(
            sql, uuid7str(), user_id, story_id, title
        )
        return ChatThreadRow.model_validate(dict(row))

    async def get_thread(
        self, 
        thread_id: str,
        executor: Executor | None = None
    ) -> Optional[ChatThreadRow]:
        sql = """
        SELECT *
        FROM "chat_thread"
        WHERE id=$1
        """
        row = await self._exe(executor).fetchrow(sql, thread_id)
        if row is None:
            return None 
        return ChatThreadRow.model_validate(dict(row))
    
    async def list_threads_for_story(
        self,
        user_id: str,
        story_id: str, 
        executor: Executor | None = None
    ) -> List[ChatThreadRow]:
        
        sql = """
        SELECT *
        FROM "chat_thread"
        WHERE user_id=$1 AND story_id=$2
        ORDER BY updated_at DESC
        """
        rows = await self._exe(executor).fetch(sql, user_id, story_id)
        
        return [
            ChatThreadRow.model_validate(dict(row))
            for row in rows
        ]
    
    async def update_thread_title(
        self,
        thread_id: str,
        title: str,
        *,
        executor: Executor | None = None
    ) -> Optional[ChatThreadRow]:
        
        sql = """
        UPDATE "chat_thread"
        SET title=$2, updated_at=NOW()
        WHERE id=$1
        RETURNING *
        """
    
        row = await self._exe(executor).fetchrow(sql, thread_id, title)

        if row is None:
            return None

        return ChatThreadRow.model_validate(dict(row))
    

    async def touch_thread(
        self,
        thread_id: str, 
        *,
        executor: Executor | None = None
    ) -> None:
        
        sql = """
        UPDATE "chat_thread"
        SET updated_at=NOW()
        WHERE id=$1
        """
        await self._exe(executor).execute(sql, thread_id)

        
    async def delete_thread(
        self,
        thread_id: str,
        *,
        executor: Executor | None = None
    ) -> None:
        
        sql = """
        DELETE FROM "chat_thread"
        WHERE id=$1
        """
        await self._exe(executor).execute(sql, thread_id)


    async def append_message(
        self,
        thread_id: str,
        user_id: str,
        role: Literal['user', 'assistant', 'system', 'tool'],
        content: str,
        *,
        executor: Executor | None = None
    ) -> ChatMessageRow:
        
        sql = """
        INSERT INTO "chat_message" (id, thread_id, user_id, role, sequence, content)
        VALUES (
            $1,
            $2,
            $3,
            $4,
            (
                SELECT
                    COALESCE(MAX(sequence) + 1, 0)
                FROM "chat_message"
                WHERE thread_id=$2
            ),
            $5
        )
        RETURNING *
        """

        row = await self._exe(executor).fetchrow(sql, uuid7str(), thread_id, user_id, role, content)

        return ChatMessageRow.model_validate(dict(row))
    
    async def list_messages(
        self,
        thread_id: str,
        *,
        executor: Executor | None = None
    ) -> List[ChatMessageRow]:
        
        sql = """
        SELECT *
        FROM "chat_message"
        WHERE thread_id=$1
        ORDER BY sequence
        """

        rows = await self._exe(executor).fetch(sql, thread_id)

        return [
            ChatMessageRow.model_validate(dict(row))
            for row in rows
        ]
    
    async def append_tool_call(
        self,
        message_id: str,
        user_id: str,
        tool_name: str,
        arguments: dict,
        *,
        executor: Executor | None = None
    ) -> ChatToolCallRow:
        
        sql = """
        INSERT INTO "chat_tool_call" (id, message_id, user_id, tool_name, sequence, arguments)
        VALUES (
            $1,
            $2,
            $3,
            $4,
            (
                SELECT
                    COALESCE(MAX(sequence) + 1, 0)
                FROM "chat_tool_call"
                WHERE message_id=$2
            ),
            $5   
        )
        RETURNING *
        """

        row = await self._exe(executor).fetchrow(
            sql,
            uuid7str(),
            message_id,
            user_id,
            tool_name,
            json.dumps(arguments)
        )

        return ChatToolCallRow.model_validate(dict(row))
    
    async def update_tool_call_result(
        self,
        tool_call_id: str,
        *,
        result: dict | None = None,
        error: str | None = None,
        executor: Executor | None = None
    ) -> None:
        
        sql = """
        UPDATE "chat_tool_call"
        SET result=COALESCE($2::jsonb, result),
            error=COALESCE($3, error)
        WHERE id=$1
        """
        await self._exe(executor).execute(
            sql, 
            tool_call_id, 
            json.dumps(result) if result is not None else None, 
            error
        )

    async def list_tool_calls_for_message(
        self,
        message_id: str,
        *,
        executor: Executor | None = None
    ) -> List[ChatToolCallRow]:
        
        sql = """
        SELECT *
        FROM "chat_tool_call"
        WHERE message_id=$1
        ORDER BY sequence
        """

        rows = await self._exe(executor).fetch(sql, message_id)

        return [
            ChatToolCallRow.model_validate(dict(row))
            for row in rows
        ]