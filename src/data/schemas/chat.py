from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from datetime import datetime


# ---------------------------------------------------------------------------
# DB row models
# ---------------------------------------------------------------------------

class ChatThreadRow(BaseModel):
    id: str
    user_id: str
    story_id: str
    title: str
    created_at: datetime
    updated_at: datetime


class ChatMessageRow(BaseModel):
    """One pydantic-ai ModelMessage persisted as JSONB.

    `message` is the dict produced by
    `ModelMessagesTypeAdapter.dump_python([msg])[0]` (or equivalently
    `msg.model_dump(mode="json")`). To replay a thread, fetch rows
    ordered by `sequence`, collect their `message` dicts into a list,
    and pass to `ModelMessagesTypeAdapter.validate_python(...)`.
    """

    id: str
    thread_id: str
    user_id: str
    sequence: int = Field(ge=0)
    kind: Literal["request", "response"]
    message: dict
    created_at: datetime


# ---------------------------------------------------------------------------
# HTTP request / response DTOs
# ---------------------------------------------------------------------------

class CreateThreadRequest(BaseModel):
    story_id: str
    first_message: str


class ThreadResponse(BaseModel):
    thread_id: str
    thread_title: str
    updated_at: datetime


class ThreadListResponse(BaseModel):
    threads: Optional[List[ThreadResponse]] = []


class ChatMessageResponse(BaseModel):
    """Pass-through of the stored ModelMessage. Front-end renders parts."""

    sequence: int
    kind: Literal["request", "response"]
    message: dict
    created_at: datetime


class ChatMessageListResponse(BaseModel):
    messages: Optional[List[ChatMessageResponse]] = []


class ConversationTurnRequest(BaseModel):
    story_id: str
    thread_id: str
    user_message: str


# ---------------------------------------------------------------------------
# HTTP request bodies (path supplies story_id / thread_id)
# ---------------------------------------------------------------------------

class CreateThreadBody(BaseModel):
    first_message: str


class TurnBody(BaseModel):
    user_message: str


class RenameThreadBody(BaseModel):
    title: str