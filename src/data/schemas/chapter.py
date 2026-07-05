from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from typing import List, Optional
from datetime import datetime
from src.data.schemas._base import ApiModel
from src.data.schemas.enums import StoryStatus


class ChapterRow(BaseModel):
    """One row from the `chapter` table."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    story_id: str
    user_id: str
    title: str
    content: str
    published: bool
    word_count: int
    next_chapter_id: Optional[str]
    prev_chapter_id: Optional[str]
    scenes_need_reextraction: bool = False
    scenes_extracted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class CreateChapterRequest(ApiModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = ""


class UpdateChapterRequest(ApiModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    content: Optional[str] = None
    published: Optional[bool] = None


class ReorderChapterRequest(ApiModel):
    from_pos: int
    to_pos: int


class ChapterListItem(ApiModel):
    story_id: str
    chapter_id: str
    chapter_number: int
    word_count: int
    story_title: str
    chapter_title: str 
    published: bool
    updated_at: datetime

  


class ChapterContentResponse(ApiModel):
    id: str
    chapter_number: int
    title: str
    published: bool
    content: str
    story_id: str
    story_title: str
    word_count: int
    created_at: datetime
    updated_at: datetime
    previous_chapter_id: Optional[str] = None
    next_chapter_id: Optional[str] = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,  # Allows using both snake_case and camelCase
    )

    @classmethod
    def from_chapter(
        cls,
        chapter: ChapterRow,
        chapter_number: int,
        story_title: str,
        *,
        content: Optional[str] = None
    ) -> "ChapterContentResponse":
        return cls(
            id=chapter.id,
            chapter_number=chapter_number,
            title=chapter.title,
            published=chapter.published,
            content=chapter.content if content is None else content,
            story_id=chapter.story_id,
            word_count=chapter.word_count,
            story_title=story_title,
            created_at=chapter.created_at,
            updated_at=chapter.updated_at,
            previous_chapter_id=chapter.prev_chapter_id,
            next_chapter_id=chapter.next_chapter_id,
        )


class ChapterListResponse(ApiModel):
    story_id: str
    story_title: str
    story_status: StoryStatus
    story_last_updated: datetime
    chapters: List[ChapterListItem]

    @classmethod
    def from_story(
        cls, story, chapters: List[ChapterListItem]
    ) -> "ChapterListResponse":
        return cls(
            story_id=story.id,
            story_title=story.title,
            story_status=story.status,
            story_last_updated=story.updated_at,
            chapters=chapters,
        )

class ChapterSummaryResponse(ApiModel):
    summary: str