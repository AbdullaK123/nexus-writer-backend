import asyncpg
from typing import Any, List, Literal, Optional
from uuid_extensions import uuid7str
import json
from src.data.schemas.chat import ChatMessageRow, ChatThreadRow

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
        user_id: str,
        executor: Executor | None = None
    ) -> Optional[ChatThreadRow]:
        sql = """
        SELECT *
        FROM "chat_thread"
        WHERE id=$1 AND user_id=$2
        """
        row = await self._exe(executor).fetchrow(sql, thread_id, user_id)
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
        user_id: str,
        title: str,
        *,
        executor: Executor | None = None
    ) -> Optional[ChatThreadRow]:
        
        sql = """
        UPDATE "chat_thread"
        SET title=$3, updated_at=NOW()
        WHERE id=$1 AND user_id=$2
        RETURNING *
        """
    
        row = await self._exe(executor).fetchrow(sql, thread_id, user_id, title)

        if row is None:
            return None

        return ChatThreadRow.model_validate(dict(row))
    

    async def touch_thread(
        self,
        thread_id: str, 
        user_id: str,
        *,
        executor: Executor | None = None
    ) -> None:
        
        sql = """
        UPDATE "chat_thread"
        SET updated_at=NOW()
        WHERE id=$1 AND user_id=$2
        """
        await self._exe(executor).execute(sql, thread_id, user_id)

        
    async def delete_thread(
        self,
        thread_id: str,
        user_id: str,
        *,
        executor: Executor | None = None
    ) -> None:
        
        sql = """
        DELETE FROM "chat_thread"
        WHERE id=$1 AND user_id=$2
        """
        await self._exe(executor).execute(sql, thread_id, user_id)


    async def append_message(
        self,
        thread_id: str,
        user_id: str,
        kind: Literal["request", "response"],
        message: dict,
        *,
        executor: Executor | None = None,
    ) -> ChatMessageRow:
        """Append one pydantic-ai ModelMessage to a thread.

        `message` must be the dict produced by
        `ModelMessagesTypeAdapter.dump_python([msg])[0]` (or
        `msg.model_dump(mode="json")`). `kind` matches pydantic-ai's
        ModelMessage discriminator and must agree with the dict's own
        `"kind"` field; we accept it explicitly so the column is indexable.
        """

        sql = """
        INSERT INTO "chat_message" (id, thread_id, user_id, sequence, kind, message)
        VALUES (
            $1,
            $2,
            $3,
            (
                SELECT COALESCE(MAX(sequence) + 1, 0)
                FROM "chat_message"
                WHERE thread_id=$2::varchar
            ),
            $4,
            $5::jsonb
        )
        RETURNING *
        """

        row = await self._exe(executor).fetchrow(
            sql,
            uuid7str(),
            thread_id,
            user_id,
            kind,
            json.dumps(message),
        )

        parsed = dict(row)
        parsed["message"] = json.loads(parsed["message"])
        return ChatMessageRow.model_validate(parsed)

    async def list_messages(
        self,
        thread_id: str,
        user_id: str,
        *,
        executor: Executor | None = None,
    ) -> List[ChatMessageRow]:
        sql = """
        SELECT *
        FROM "chat_message"
        WHERE thread_id=$1 AND user_id=$2
        ORDER BY sequence
        """

        rows = await self._exe(executor).fetch(sql, thread_id, user_id)

        out: List[ChatMessageRow] = []
        for row in rows:
            d = dict(row)
            d["message"] = json.loads(d["message"])
            out.append(ChatMessageRow.model_validate(d))
        return out