from sqlmodel import SQLModel, Relationship, Field, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy import JSON, Column, String
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
    user: 'User' = Relationship(back_populates='sessions', sa_relationship_kwargs={"lazy": "raise"})


class User(SQLModel, TimeStampMixin, table=True):
    id: Optional[str] = Field(default_factory=generate_uuid, primary_key=True)
    username: str
    email: EmailStr = Field(index=True, unique=True)
    password_hash: str
    profile_img: Optional[str] = Field(default=None, unique=True)
    sessions: List['Session'] = Relationship(back_populates='user', cascade_delete=True, sa_relationship_kwargs={"lazy": "raise"})
    stories: List['Story'] = Relationship(back_populates='user', cascade_delete=True, sa_relationship_kwargs={"lazy": "raise"})
    chapters: List['Chapter'] = Relationship(back_populates='user', cascade_delete=True, sa_relationship_kwargs={"lazy": "raise"})
    targets: List['Target'] = Relationship(back_populates='user', cascade_delete=True, sa_relationship_kwargs={"lazy": "raise"})
    

class Story(SQLModel, TimeStampMixin, table=True):

    __table_args__ = (
        UniqueConstraint('user_id', 'title'),
    )

    id: Optional[str] = Field(default_factory=generate_uuid, primary_key=True)
    user_id: str = Field(index=True, foreign_key='user.id', ondelete='CASCADE')
    title: str = Field(index=True)
    story_context: Optional[str] = Field(default=None)
    status: StoryStatus = Field(default=StoryStatus.ONGOING)
    path_array: Optional[List[str]] = Field(sa_column=Column(ARRAY(String)))
    chapters: List['Chapter'] = Relationship(back_populates='story', cascade_delete=True, sa_relationship_kwargs={"lazy": "raise"})
    user: 'User' = Relationship(back_populates='stories', sa_relationship_kwargs={"lazy": "raise"})
    target: 'Target' = Relationship(back_populates='story', cascade_delete=True, sa_relationship_kwargs={"lazy": "raise"})


class Chapter(SQLModel, TimeStampMixin, table=True):

    __table_args__ = (
        UniqueConstraint('user_id', 'story_id', 'title'),
        CheckConstraint('id != prev_chapter_id', name='no_self_prev_reference'),
        CheckConstraint('id != next_chapter_id', name='no_self_next_reference'),
        CheckConstraint(
            'prev_chapter_id != next_chapter_id OR prev_chapter_id IS NULL OR next_chapter_id IS NULL', 
            name='no_circular_prev_next'
        ),
    )

    # Primary fields
    id: Optional[str] = Field(default_factory=generate_uuid, primary_key=True)
    story_id: str = Field(index=True, foreign_key='story.id', ondelete='CASCADE')
    user_id: str = Field(index=True, foreign_key='user.id', ondelete='CASCADE')
    title: str 
    content: str  # Raw chapter text
    published: bool = Field(default=False)
    
    # Word count tracking
    word_count: int = Field(default=0, description="Current word count")
    last_extracted_word_count: Optional[int] = Field(
        default=None, 
        description="Word count at last extraction (for delta checking)"
    )
    
    # Condensed context (rolling context extraction result)
    condensed_context: Optional[str] = Field(
        default=None,
        description="Final 1500-word condensed context in structured prose"
    )
    timeline_context: Optional[str] = Field(
        default=None,
        description="When this chapter occurs in the story timeline"
    )
    emotional_arc: Optional[str] = Field(
        default=None,
        description="Emotional journey of the chapter"
    )
    
    # Extraction metadata
    last_extracted_at: Optional[datetime] = Field(
        default=None,
        description="When extraction was last run"
    )
    extraction_version: Optional[str] = Field(
        default=None,
        description="Version of extraction prompts used (e.g., '1.0.0')"
    )
    
    # Relationships
    story: 'Story' = Relationship(back_populates='chapters', sa_relationship_kwargs={"lazy": "raise"})
    user: 'User' = Relationship(back_populates='chapters', sa_relationship_kwargs={"lazy": "raise"})
    
    # Linked list for chapter ordering
    next_chapter_id: Optional[str] = Field(
        default=None, 
        foreign_key="chapter.id", 
        ondelete='SET NULL'
    )
    prev_chapter_id: Optional[str] = Field(
        default=None, 
        foreign_key="chapter.id", 
        ondelete='SET NULL'
    )
    
    @staticmethod
    def get_chapter_number(chapter_id: str, path_array: Optional[List[str]]) -> int:
        """Get chapter number from a story's path_array without traversing relationships."""
        if not path_array:
            return 1
        try:
            return path_array.index(chapter_id) + 1
        except ValueError as e:
            raise ValueError(
                f"Chapter {chapter_id} not found in path_array. "
                f"Expected one of: {path_array}"
            ) from e
    
    @property
    def has_extractions(self) -> bool:
        """Check if extraction is complete (condensed context exists)"""
        return bool(self.condensed_context)


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
    story: 'Story' = Relationship(back_populates='target', sa_relationship_kwargs={"lazy": "raise"})
    user: 'User' = Relationship(back_populates='targets', sa_relationship_kwargs={"lazy": "raise"})



