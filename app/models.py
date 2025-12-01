from sqlmodel import SQLModel, Relationship, Field, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import Column, String
from pydantic import EmailStr
from datetime import datetime
from typing import Literal, Optional, List
import uuid
from enum import Enum


def generate_uuid():
    return str(uuid.uuid4())

class StoryStatus(str, Enum):
    COMPLETE = "Complete"
    ON_HAITUS = "On Hiatus"
    ONGOING = "Ongoing"

class FrequencyType(str, Enum):
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"


class TimeStampMixin:
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


class Session(SQLModel, TimeStampMixin,  table=True):
    session_id: str = Field(index=True, primary_key=True)
    user_id: str = Field(index=True, foreign_key='user.id', ondelete='CASCADE')
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
    sessions: List['Session'] = Relationship(back_populates='user', cascade_delete=True)
    stories: List['Story'] = Relationship(back_populates='user', cascade_delete=True)
    chapters: List['Chapter'] = Relationship(back_populates='user', cascade_delete=True)
    targets: List['Target'] = Relationship(back_populates='user', cascade_delete=True)
    

class Story(SQLModel, TimeStampMixin, table=True):

    __table_args__ = (
        UniqueConstraint('user_id', 'title'),
    )

    id: Optional[str] = Field(default_factory=generate_uuid, primary_key=True)
    user_id: str = Field(index=True, foreign_key='user.id', ondelete='CASCADE')
    title: str = Field(index=True)
    story_context: str
    status: StoryStatus = Field(default=StoryStatus.ONGOING)
    path_array: Optional[List[str]] = Field(sa_column=Column(ARRAY(String)))
    chapters: List['Chapter'] = Relationship(back_populates='story', cascade_delete=True)
    user: 'User' = Relationship(back_populates='stories')
    target: 'Target' = Relationship(back_populates='story', cascade_delete=True)


class Chapter(SQLModel, TimeStampMixin, table=True):

    __table_args__ = (
        UniqueConstraint('user_id', 'story_id', 'title'),
        CheckConstraint('id != prev_chapter_id', name='no_self_prev_reference'), # No self referencing
        CheckConstraint('id != next_chapter_id', name='no_self_next_reference'), # No self referencing
        CheckConstraint(
            'prev_chapter_id != next_chapter_id OR prev_chapter_id IS NULL OR next_chapter_id IS NULL', 
            name='no_circular_prev_next'
        ), # no circular or non existent refs
    )


    id: Optional[str] = Field(default_factory=generate_uuid, primary_key=True)
    story_id: str = Field(index=True, foreign_key='story.id', ondelete='CASCADE')
    user_id: str = Field(index=True, foreign_key='user.id', ondelete='CASCADE')
    title: str 
    content: str
    chapter_context: str
    published: bool = Field(default=False)
    story: 'Story' = Relationship(back_populates='chapters')
    user: 'User' = Relationship(back_populates='chapters')
    next_chapter_id: Optional[str] = Field(default=None, foreign_key="chapter.id", ondelete='SET NULL')
    prev_chapter_id: Optional[str] = Field(default=None, foreign_key="chapter.id", ondelete='SET NULL')


class Target(SQLModel, TimeStampMixin, table=True):

    __table_args__ = (
        UniqueConstraint('story_id', 'frequency'),
        CheckConstraint('to_date >= from_date', name='to_date_gte_from_date')
    )

    id: Optional[str] = Field(default_factory=generate_uuid, primary_key=True)
    story_id: str = Field(index=True, foreign_key='story.id', ondelete='CASCADE')
    user_id: str = Field(index=True, foreign_key='user.id', ondelete='CASCADE')
    quota: int = Field(ge=0, default=0, description="Word count target")
    frequency: FrequencyType = Field(default="Daily", description="Frequency of word count quota")
    from_date: datetime = Field(default_factory=datetime.utcnow)
    to_date: datetime = Field(default_factory=datetime.utcnow)
    story: 'Story' = Relationship(back_populates='target')
    user: 'User' = Relationship(back_populates='targets')



