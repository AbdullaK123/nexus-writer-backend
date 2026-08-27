from datetime import datetime, timezone

import pytest

from src.data.schemas.scene import SceneRow
from tests.service.mocks import FakeSceneRepository


@pytest.fixture
def pending_scenes(fake_scene_repo: FakeSceneRepository) -> list[SceneRow]:
    current = datetime.now(timezone.utc)
    scenes = [
        SceneRow(
            id="scene-1",
            chapter_id="chapter-1",
            story_id="story-1",
            user_id="user-1",
            position=0,
            title="The Eastern Gate",
            start_quote="Aria reached the gate.",
            end_quote="The bell rang.",
            description="Aria reaches the eastern gate and finds it unguarded.",
            pov="Aria",
            word_count=120,
            tension="medium",
            pacing="steady",
            mentioned_entities=["Aria", "Eastern Gate"],
            tags=["mystery", "worldbuilding"],
            questions_raised=["Who opened the eastern gate?"],
            embedding_model=None,
            embedded_at=None,
            created_at=current,
            updated_at=current,
        ),
        SceneRow(
            id="scene-2",
            chapter_id="chapter-1",
            story_id="story-1",
            user_id="user-1",
            position=1,
            title="The Council Chamber",
            start_quote="Beren entered the chamber.",
            end_quote="The doors closed.",
            description="Beren enters the council chamber for a secret meeting.",
            pov="Beren",
            word_count=140,
            tension="high",
            pacing="fast",
            mentioned_entities=["Beren", "Council"],
            tags=["politics", "plot-revelation"],
            questions_raised=["Why was the council summoned?"],
            embedding_model=None,
            embedded_at=None,
            created_at=current,
            updated_at=current,
        ),
    ]
    for scene in scenes:
        fake_scene_repo.seed(scene)
    return scenes


@pytest.fixture
def current_scene(fake_scene_repo: FakeSceneRepository) -> SceneRow:
    current = datetime.now(timezone.utc)
    scene = SceneRow(
        id="scene-current",
        chapter_id="chapter-2",
        story_id="story-1",
        user_id="user-1",
        position=0,
        title="Already Embedded",
        start_quote="The river was quiet.",
        end_quote="Dawn arrived.",
        description="A quiet connective scene by the river.",
        pov="Aria",
        word_count=80,
        tension="low",
        pacing="slow",
        mentioned_entities=["Aria"],
        tags=["reflection"],
        questions_raised=[],
        embedding_model="test-embedding-model",
        embedded_at=current,
        created_at=current,
        updated_at=current,
    )
    fake_scene_repo.seed(scene)
    return scene
