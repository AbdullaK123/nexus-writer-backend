from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
from typing import Optional

class LineEdit(BaseModel):
    paragraph_idx: int = Field(description="The index of the paragraph you are editing.")
    original_paragraph: str = Field(description="The original, unedited paragraph.")
    edited_paragraph: str = Field(description="The edited paragraph")
    justification: str = Field(description="Your justification for the edit.")


class ChapterEdit(BaseModel):
    edits: List[LineEdit]
    last_generated_at: datetime | None
    is_stale: bool = Field(
        default=False,
        description="Indicates if content has changed since edits were generated"
    )

class ChapterEdits(BaseModel):
    chapter_id: str
    story_id: str
    chapter_number: int 
    
    edits: List[LineEdit] = []
    last_generated_at: Optional[datetime] = None
    is_stale: bool = False





