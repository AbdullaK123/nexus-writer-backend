from pydantic import BaseModel, Field
from typing import List
from app.agents.tools.prose import calculate_readability_metrics


class ReadabilityMetrics(BaseModel):
    word_count: int = Field(description="The word count for the text.")
    sentence_count: int = Field(description="The sentence count for the text.")
    flesch_reading_ease: float = Field(description="The Flesch Reading Ease score for the text.")
    smog_index: float = Field(description="The SMOG Index score for the text.")
    coleman_liau_index: float = Field(description="The Coleman-Liau Index score for the text.")
    automated_readability_index: float = Field(description="The Automated Readability Index score for the text.")
    linsear_write_formula: float = Field(description="The Linsear Write Formula score for the text.")
    gunning_fog_index: float = Field(description="The Gunning Fog Index score for the text.")
    dale_chall_readability_score: float = Field(description="The Dale Chall Readability Score for the text.")
    text_standard: str = Field(description="The text standard for the text.")

    def get_text_standard(self):
        if self.flesch_reading_ease >= 90:
            interpretation = "Very Easy (5th grade)"
        elif self.flesch_reading_ease >= 80:
            interpretation = "Easy (6th grade)"
        elif self.flesch_reading_ease >= 70:
            interpretation = "Fairly Easy (7th grade)"
        elif self.flesch_reading_ease >= 60:
            interpretation = "Standard (8th-9th grade)"
        elif self.flesch_reading_ease >= 50:
            interpretation = "Fairly Difficult (10th-12th grade)"
        elif self.flesch_reading_ease >= 30:
            interpretation = "Difficult (College)"
        else:
            interpretation = "Very Difficult (College graduate)"
        self.text_standard = interpretation

    def model_post_init(self, __context: dict):
        self.get_text_standard()

    @classmethod
    def from_text(cls, text: str):
        metrics = calculate_readability_metrics.invoke(text)
        return cls(**metrics)

class ParagraphEdit(BaseModel):
    paragraph_idx: int = Field(description="The index of the paragraph you are editing.")
    original_text: str = Field(description="The original, unedited text of the paragraph.")
    edited_text: str = Field(description="Your improved, edited version of the original paragraph.")
    justification: str = Field(description="Your justification for why your edited paragraph is better.")

class ChapterEdit(BaseModel):
    paragraph_edits: List[ParagraphEdit]

class ChapterEditResponse(BaseModel):
    edits: ChapterEdit
    before_metrics: ReadabilityMetrics
    after_metrics: ReadabilityMetrics
    execution_time: float
    from_cache: bool = Field(default=False, description="Whether the chapter edits were retrieved from cache.")