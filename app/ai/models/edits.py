from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

class LineEdit(BaseModel):
    paragraph_idx: int = Field(description="The index of the paragraph you are editing.")
    original_paragraph: str = Field(description="The original, unedited paragraph.")
    edited_paragraph: str = Field(description="The edited paragraph")
    justification: str = Field(description="Your justification for the edit.")


class ChapterEdit(BaseModel):
    edits: List[LineEdit]
    last_generated_at: datetime





