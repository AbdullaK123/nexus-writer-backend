from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from src.app.dependencies import get_verified_user, get_chat_service
from src.app.dependencies.rate_limit import ai_rate_limit, write_rate_limit
from src.data.schemas import UserRow
from src.data.schemas.chat import (
    ChatMessageListResponse,
    ConversationTurnRequest,
    CreateThreadBody,
    CreateThreadRequest,
    RenameThreadBody,
    ThreadListResponse,
    ThreadResponse,
    TurnBody,
)
from src.service.chat import ChatService

chat_controller = APIRouter(prefix="/{story_id}/chat")

@chat_controller.post("/threads", response_model=ThreadResponse, dependencies=[write_rate_limit])
async def create_thread(
    story_id: str,
    body: CreateThreadBody,
    current_user: UserRow = Depends(get_verified_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> ThreadResponse:
    return await chat_service.create_thread(
        current_user.id,
        CreateThreadRequest(
            story_id=story_id,  # type: ignore
            first_message=body.first_message,  # type: ignore
        ),
    )

@chat_controller.get("/threads", response_model=ThreadListResponse)
async def list_threads(
    story_id: str,
    current_user: UserRow = Depends(get_verified_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> ThreadListResponse:
    return await chat_service.get_threads(story_id, current_user.id)

@chat_controller.get("/threads/{thread_id}/messages", response_model=ChatMessageListResponse)
async def list_thread_messages(
    story_id: str,
    thread_id: str,
    current_user: UserRow = Depends(get_verified_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatMessageListResponse:
    return await chat_service.get_thread_messages(
        thread_id=thread_id,
        user_id=current_user.id,
        story_id=story_id,
    )

@chat_controller.patch("/threads/{thread_id}", response_model=ThreadResponse, dependencies=[write_rate_limit])
async def rename_thread(
    story_id: str,
    thread_id: str,
    body: RenameThreadBody,
    current_user: UserRow = Depends(get_verified_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> ThreadResponse:
    return await chat_service.update_thread_title(
        thread_id=thread_id,
        user_id=current_user.id,
        new_title=body.title,
        story_id=story_id,
    )

@chat_controller.delete("/threads/{thread_id}", response_model=dict, dependencies=[write_rate_limit])
async def delete_thread(
    story_id: str,
    thread_id: str,
    current_user: UserRow = Depends(get_verified_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> dict:
    return await chat_service.delete_thread(
        thread_id=thread_id,
        user_id=current_user.id,
        story_id=story_id,
    )

@chat_controller.post("/threads/{thread_id}/turn", dependencies=[ai_rate_limit])
async def stream_turn(
    story_id: str,
    thread_id: str,
    body: TurnBody,
    current_user: UserRow = Depends(get_verified_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> StreamingResponse:
    payload = ConversationTurnRequest(
        story_id=story_id,
        thread_id=thread_id,
        user_message=body.user_message,
    )
    return StreamingResponse(
        chat_service.stream_turn_sse(current_user.id, payload),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
