
from typing import AsyncIterator
import json
from pydantic_ai import Agent, ModelMessagesTypeAdapter
from src.data.schemas.chat import ChatMessageListResponse, ChatMessageResponse, ConversationTurnRequest, ThreadListResponse
from src.infrastructure.ai.providers.protocol import AIProvider
from src.data.repositories import ChatRepository, StoryRepository
from src.data.schemas import CreateThreadRequest, ThreadResponse
from src.service.chat.agent import ChatDeps
from src.service.exceptions import ForbiddenError, NotFoundError, ServiceError, ValidationError
from src.service.chapter import ChapterService
from src.service.story import StoryService
from loguru import logger

from src.service.utils.decorators import handle_service_errors, handle_service_errors_stream

class ChatService:

    def __init__(
        self,
        provider: AIProvider,
        chat_repo: ChatRepository,
        story_repo: StoryRepository,
        chapter_service: ChapterService,
        story_service: StoryService,
        agent: Agent[ChatDeps, str]
    ) -> None:
        self._provider = provider
        self._chat_repo = chat_repo
        self._story_repo = story_repo
        self._story_svc = story_service
        self._chapter_svc = chapter_service
        self._agent = agent

    @handle_service_errors
    async def create_thread(
        self,
        user_id: str,
        payload: CreateThreadRequest
    ) -> ThreadResponse:
        
        try:
            title = await self._provider.generate(
                system_prompt="""
                You are a terse title generator
                """,
                text=f"""
                Generate a title for a conversation thread 
                with the following initial message in triple backticks:
                ```{payload.first_message}```
                """,
                max_tokens=50 # will tune later
            )
        except Exception as e:
            logger.warning("svc.create_thread.generate_title.failed", error=str(e))
            title = payload.first_message[:20] + "..."

        story = await self._story_repo.get(payload.story_id, user_id)
        if story is None:
            raise NotFoundError("Story not found")

        thread = await self._chat_repo.create_thread(
            user_id,
            payload.story_id,
            title
        )

        return ThreadResponse(
            thread_id=thread.id,
            thread_title=thread.title,
            updated_at=thread.updated_at
        )
    
    @handle_service_errors    
    async def update_thread_title(
        self,
        thread_id: str,
        user_id: str,
        new_title: str 
    ) -> ThreadResponse:
        
        updated_thread = await self._chat_repo.update_thread_title(thread_id, user_id, new_title)

        if updated_thread is None:
            raise NotFoundError("Thread not found")

        return ThreadResponse(
            thread_id=updated_thread.id,
            thread_title=updated_thread.title,
            updated_at=updated_thread.updated_at
        )
    
    @handle_service_errors
    async def delete_thread(
        self,
        thread_id: str,
        user_id: str
    ) -> dict:
        
        thread = await self._chat_repo.get_thread(thread_id, user_id)

        if thread is None:
            raise NotFoundError("Thread not found")
        
        await self._chat_repo.delete_thread(thread_id, user_id)

        return {
            "message": "Thread successfully deleted."
        }
    
    @handle_service_errors
    async def get_threads(
        self,
        story_id: str,
        user_id: str
    ) -> ThreadListResponse:

        story = await self._story_repo.get(story_id, user_id)

        if story is None:
            raise NotFoundError("Story not found")
        
        threads = await self._chat_repo.list_threads_for_story(user_id, story_id)

        return ThreadListResponse(
            threads=[
                ThreadResponse(
                    thread_id=thread.id,
                    thread_title=thread.title,
                    updated_at=thread.updated_at
                )
                for thread in threads
            ]
        )
    
    @handle_service_errors
    async def get_thread_messages(
        self,
        thread_id: str,
        user_id: str
    ) -> ChatMessageListResponse:
        
        thread = await self._chat_repo.get_thread(thread_id, user_id)

        if thread is None:
            raise NotFoundError("Thread not found error")
        
        messages = await self._chat_repo.list_messages(thread_id, user_id)

        return ChatMessageListResponse(
            thread_id=thread.id,
            thread_title=thread.title,
            messages=[
                ChatMessageResponse(
                    sequence=message.sequence,
                    kind=message.kind,
                    message=message.message,
                    created_at=message.created_at,
                )
                for message in messages
            ]
        )

    @handle_service_errors_stream
    async def run_turn(
        self,
        user_id: str,
        payload: ConversationTurnRequest
    ) -> AsyncIterator[str]:
        
        async with self._chat_repo.pool.acquire() as conn:

            story = await self._story_repo.get(payload.story_id, user_id, executor=conn)

            if story is None:
                raise NotFoundError("Story not found")
            
            thread = await self._chat_repo.get_thread(
                payload.thread_id, 
                user_id, 
                executor=conn
            )

            if thread is None:
                raise NotFoundError("Thread not found")
            
            if payload.story_id != thread.story_id:
                raise ValidationError({"story_id": ["does not match thread"]})
            
            rows = await self._chat_repo.list_messages(
                payload.thread_id,
                user_id,
                executor=conn
            )

        history = ModelMessagesTypeAdapter.validate_python([r.message for r in rows])

        deps = ChatDeps(
            user_id=user_id,
            story_id=payload.story_id,
            chapter_service=self._chapter_svc,
            story_service=self._story_svc
        )

        async with self._agent.run_stream(
            user_prompt=payload.user_message,
            deps=deps,
            message_history=history
        ) as stream:
            async for delta in stream.stream_text(delta=True):
                yield delta
            new_messages = stream.new_messages()
        
        serialized = ModelMessagesTypeAdapter.dump_python(new_messages, mode="json")

        async with self._chat_repo.pool.acquire() as conn:
            async with conn.transaction():
                for msg, dumped in zip(new_messages, serialized, strict=True):
                    await self._chat_repo.append_message(
                        thread_id=payload.thread_id,
                        user_id=user_id,
                        kind=msg.kind,
                        message=dumped,
                        executor=conn
                    )
                await self._chat_repo.touch_thread(
                    payload.thread_id,
                    user_id,
                    executor=conn
                )

    @staticmethod
    def _sse_frame(event: str, data: dict) -> str:
        return f"event: {event}\ndata: {json.dumps(data)}\n\n"

    async def stream_turn_sse(
        self,
        user_id: str,
        payload: ConversationTurnRequest,
    ) -> AsyncIterator[str]:
        """Run a turn and yield Server-Sent Events frames.

        Frames:
            event: token  data: {"delta": "..."}    — model text chunk
            event: done   data: {}                   — turn finished cleanly
            event: error  data: {"code", "message"}  — ServiceError raised

        ServiceError is caught and emitted as an `error` frame so the SSE
        stream closes cleanly: by the time `run_turn` starts yielding, the
        response headers have already been flushed and the global FastAPI
        exception handler can no longer turn the failure into an HTTP
        status code."""
        try:
            async for delta in self.run_turn(user_id, payload):
                yield self._sse_frame("token", {"delta": delta})
        except ServiceError as e:
            logger.warning(
                "svc.chat.stream_turn_sse.service_error",
                code=e.code,
                message=e.message,
            )
            err: dict = {"code": e.code, "message": e.message}
            fields = getattr(e, "fields", None)
            if fields:
                err["fields"] = fields
            yield self._sse_frame("error", err)
            return
        except Exception:
            logger.exception("svc.chat.stream_turn_sse.unhandled")
            yield self._sse_frame(
                "error",
                {"code": "INTERNAL", "message": "Internal server error"},
            )
            return
        yield self._sse_frame("done", {})