from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
from typing import Optional

class LineEdit(BaseModel):
    paragraph_idx: int = Field(description="Zero-based index of the paragraph being edited, corresponding to its position in the chapter's paragraph list")
    original_paragraph: str = Field(description="The exact, unmodified paragraph text as it appears in the chapter — must match the source verbatim for diffing")
    edited_paragraph: str = Field(description="The revised paragraph with line-level prose improvements applied (e.g., tighter wording, stronger verbs, better rhythm). Must preserve the original meaning and plot content.")
    justification: str = Field(description="A concise explanation of what was changed and why — cite the specific craft issue addressed (e.g., 'Replaced filter words', 'Broke up run-on sentence', 'Converted telling to showing')")


class ChapterEdit(BaseModel):
    edits: List[LineEdit] = Field(default=[])

class ChapterEditResponse(BaseModel):
    edits: List[LineEdit]
    last_generated_at: Optional[datetime] = None
    is_stale: bool = False
  
class ChapterEdits(BaseModel):
    chapter_id: str
    story_id: str
    chapter_number: int 
    
    edits: List[LineEdit] = Field(default=[])
    last_generated_at: Optional[datetime] = None
    is_stale: bool = False





