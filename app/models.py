from sqlmodel import SQLModel, Relationship, Field, UniqueConstraint
from pydantic import EmailStr, AnyUrl
from datetime import datetime
from typing import Optional, List
import uuid
from enum import Enum


def generate_uuid():
    return str(uuid.uuid4())

class StoryStatus(str, Enum):
    COMPLETE = "Complete"
    ON_HAITUS = "On Hiatus"
    ONGOING = "Ongoing"

class TimeStampMixin:
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


class Session(SQLModel, TimeStampMixin,  table=True):
    session_id: str = Field(index=True, primary_key=True)
    user_id: str = Field(index=True, foreign_key='user.id')
    expires_at: datetime
    ip_address: Optional[str] = Field(default=None)
    user_agent: Optional[str] = Field(default=None)
    user: 'User' = Relationship(back_populates='sessions')


class User(SQLModel, TimeStampMixin, table=True):
    id: Optional[str] = Field(default_factory=generate_uuid, primary_key=True)
    username: str
    email: EmailStr = Field(index=True, unique=True)
    password_hash: str
    profile_img: Optional[str] = Field(default=None, unique=True)
    sessions: List['Session'] = Relationship(back_populates='user')
    stories: List['Story'] = Relationship(back_populates='user')
    chapters: List['Chapter'] = Relationship(back_populates='user')
    

class Story(SQLModel, TimeStampMixin, table=True):

    __table_args__ = (
        UniqueConstraint('user_id', 'title'),
    )

    id: Optional[str] = Field(default_factory=generate_uuid, primary_key=True)
    user_id: str = Field(index=True, foreign_key='user.id')
    title: str = Field(index=True)
    status: StoryStatus = Field(default=StoryStatus.ONGOING)
    chapters: List['Chapter'] = Relationship(back_populates='story')
    user: 'User' = Relationship(back_populates='stories')


class Chapter(SQLModel, TimeStampMixin, table=True):

    __table_args__ = (
        UniqueConstraint('user_id', 'story_id', 'title'),
    )


    id: Optional[str] = Field(default_factory=generate_uuid, primary_key=True)
    story_id: str = Field(index=True, foreign_key='story.id')
    user_id: str = Field(index=True, foreign_key='user.id')
    title: str 
    content: str
    published: bool = Field(default=False)
    story: 'Story' = Relationship(back_populates='chapters')
    user: 'User' = Relationship(back_populates='chapters')
    next_chapter_id: Optional[str] = Field(default=None, foreign_key="chapter.id")
    prev_chapter_id: Optional[str] = Field(default=None, foreign_key="chapter.id")
    
    # Self-referencing relationships
    next_chapter: Optional['Chapter'] = Relationship(
        sa_relationship_kwargs={'foreign_keys': 'Chapter.next_chapter_id'}
    )
    prev_chapter: Optional['Chapter'] = Relationship(
        sa_relationship_kwargs={'foreign_keys': 'Chapter.prev_chapter_id'}
    )



