from sqlmodel import SQLModel, Field
from pydantic import model_validator
from typing import List, Optional, Literal
from app.ai.models.structure import Scene, Pacing

class SceneWithContext(Scene):
    chapter_number: int
    chapter_id: str

    @classmethod
    def from_scene(
        cls, 
        chapter_number: int,
        chapter_id: str,
        scene: Scene
    ) -> "SceneWithContext":
        return cls(
            chapter_id=chapter_id,
            chapter_number=chapter_number,
            **scene.model_dump()
        )

class SceneIndexResponse(SQLModel):
    scenes: Optional[List[SceneWithContext]] = []

class ChapterScenes(SQLModel):
    chapter_number: int
    chapter_id: str
    scenes: Optional[List[Scene]] = []


class WeakScenesResponse(SQLModel):
    weak_scenes: Optional[List[ChapterScenes]] = []


class SceneDistribution(SQLModel):
    type: Literal["action", "dialogue", "introspection", "exposition", "transition"]
    scene_count: int
    pct: float = Field(default=0.0, le=1.0)

class ChapterSceneDistribution(SQLModel):
    chapter_number: int
    chapter_id: str
    distributions: Optional[List[SceneDistribution]] = []

    @model_validator(mode="after")
    def validate_distributions(self):

        types = [dist.type for dist in self.distributions]
        
        if len(types) != len(set(types)):
            raise ValueError("Only one distribution allowed for each scene type!")

        return self
    
class SceneTypeDistributionResponse(SQLModel):
    chapter_distributions: Optional[List[ChapterSceneDistribution]] = []


class POVDistribution(SQLModel):
    pov: str
    scene_count: int 
    estimated_word_count: int
    pct: float = Field(default=0.0, le=1.0)

class ChapterPOVBalance(SQLModel):
    chapter_number: int
    chapter_id: str
    distributions: Optional[List[POVDistribution]] = []

    @model_validator(mode="after")
    def validate_distributions(self):
        povs = [dist.pov for dist in self.distributions]
        
        if len(povs) != len(set(povs)):
            raise ValueError("Only one distribution allowed for each pov!")
        
        return self

class POVBalanceResponse(SQLModel):
    chapter_distributions: Optional[List[ChapterPOVBalance]] = []


class ChapterPacingDistribution(Pacing):
    chapter_number: int
    chapter_id: str

class PacingCurveResponse(SQLModel):
    chapter_distributions: Optional[List[ChapterPacingDistribution]] = []

class ChapterRole(SQLModel):
    chapter_number: int 
    chapter_id: str
    structural_role: Literal[
        "exposition", "inciting_incident", "rising_action",
        "climax", "falling_action", "resolution", "transition", "flashback"
    ] = Field(default="exposition", description="This chapter's function in the overall story arc: 'exposition' (establishes world/characters), 'inciting_incident' (disrupts status quo), 'rising_action' (escalates conflict), 'climax' (peak confrontation), 'falling_action' (aftermath), 'resolution' (wraps up), 'transition' (bridges major story sections), 'flashback' (reveals past events)")

class StructuralArcResponse(SQLModel):
    roles: Optional[List[ChapterRole]] = []

class ThemeDistribution(SQLModel):
    chapter_ids: List[str]
    theme: str 
    count: int 
    perc: float = Field(default=0.0, le=1.0)

class ThemeDistributionResponse(SQLModel):
    theme_distributions: Optional[List[ThemeDistribution]] = []

    @model_validator(mode="after")
    def validate_distributions(self):
        themes = [dist.theme for dist in self.theme_distributions]
        
        if len(themes) != len(set(themes)):
            raise ValueError("Only one distribution allowed for each theme!")
        
        return self

class ChapterEmotionalBeats(SQLModel):
    chapter_number: int
    chapter_id: str
    strong: int = 0
    moderate: int = 0
    weak: int = 0
    strong_perc: float = 0.0
    moderate_perc: float = 0.0
    weak_perc: float = 0.0

    @model_validator(mode="after")
    def compute_percentages(self):
        total = self.weak + self.moderate + self.strong
        if total > 0:
            self.weak_perc = round(100 * self.weak / total, 2)
            self.moderate_perc = round(100 * self.moderate / total, 2)
            self.strong_perc = round(100 * self.strong / total, 2)
        return self


class EmotionalBeatsResponse(SQLModel):
    chapter_distributions: Optional[List[ChapterEmotionalBeats]] = []


class DevelopmentalReportResponse(SQLModel):
    story_id: str
    report: str = ""