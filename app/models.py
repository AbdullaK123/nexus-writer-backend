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
    character_bios: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSONB),
        description="Json array of all character bios"
    )
    plot_threads: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSONB),
        description="PlotThreadTracker - all plot threads with status, introduced/resolved chapters"
    )
    world_bible: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSONB),
        description="WorldBibleExtraction - all worldbuilding consolidated"
    )
    pacing_structure: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSONB),
        description="PacingAndStructureAnalysis result"
    )
    story_timeline: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSONB),
        description="StoryTimeline - complete temporal analysis"
    )
    status: StoryStatus = Field(default=StoryStatus.ONGOING)
    path_array: Optional[List[str]] = Field(sa_column=Column(ARRAY(String)))
    chapters: List['Chapter'] = Relationship(back_populates='story', cascade_delete=True)
    user: 'User' = Relationship(back_populates='stories')
    target: 'Target' = Relationship(back_populates='story', cascade_delete=True)


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
    themes: Optional[list[str]] = Field(
        default=None,
        sa_column=Column(JSONB),
        description="Themes explored in this chapter"
    )
    emotional_arc: Optional[str] = Field(
        default=None,
        description="Emotional journey of the chapter"
    )
    
    # Multi-pass extraction results (stored as JSONBB)
    character_extraction: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSONB),
        description="CharacterExtraction result"
    )
    plot_extraction: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSONB),
        description="PlotExtraction result"
    )
    world_extraction: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSONB),
        description="WorldExtraction result"
    )
    structure_extraction: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSONB),
        description="StructureExtraction result"
    )
    
    # Line edits (stored as JSONBB array)
    line_edits: Optional[list[dict]] = Field(
        default=None,
        sa_column=Column(JSONB),
        description="Array of LineEdit objects"
    )
    line_edits_generated_at: Optional[datetime] = Field(
        default=None,
        description="When line edits were last generated"
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
    story: 'Story' = Relationship(back_populates='chapters')
    user: 'User' = Relationship(back_populates='chapters')
    
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
    
    # Computed properties
    @property
    def needs_extraction(self) -> bool:
        """Check if chapter needs re-extraction based on word count delta"""
        if self.last_extracted_word_count is None:
            return True  # Never extracted
        
        word_delta = abs(self.word_count - self.last_extracted_word_count)
        return word_delta >= 1000
    
    @property
    def estimated_reading_time_minutes(self) -> int:
        """Calculate estimated reading time"""
        return max(1, self.word_count // 250)
    
    @property
    def has_extractions(self) -> bool:
        """Check if all extraction passes are complete"""
        return all([
            self.character_extraction,
            self.plot_extraction,
            self.world_extraction,
            self.structure_extraction,
            self.condensed_context
        ])


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



