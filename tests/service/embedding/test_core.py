from src.data.schemas.scene import SceneRow
from src.infrastructure.config import config
from src.service.embedding.service import EMBEDDING_DIMENSION, EmbeddingService
from tests.service.mocks import FakeAIProvider, FakeSceneRepository


async def test_pending_scenes_receive_embeddings_and_model_metadata(
    embedding_service: EmbeddingService,
    pending_scenes: list[SceneRow],
    fake_provider: FakeAIProvider,
    fake_scene_repo: FakeSceneRepository,
) -> None:
    fake_provider.embed_many_response = [
        [0.1] * EMBEDDING_DIMENSION,
        [0.2] * EMBEDDING_DIMENSION,
    ]

    await embedding_service.embed_pending_batched()

    assert [scene_id for scene_id, _, _ in fake_scene_repo.embedding_updates] == [
        pending_scenes[0].id,
        pending_scenes[1].id,
    ]
    assert all(
        model == fake_provider.embedding_model
        for _, _, model in fake_scene_repo.embedding_updates
    )
    first = fake_scene_repo.get(pending_scenes[0].id)
    second = fake_scene_repo.get(pending_scenes[1].id)
    assert first is not None
    assert second is not None
    assert first.embedded_at is not None
    assert second.embedded_at is not None


async def test_embedding_text_contains_scene_grounding_fields(
    embedding_service: EmbeddingService,
    pending_scenes: list[SceneRow],
    fake_provider: FakeAIProvider,
) -> None:
    await embedding_service.embed_pending_batched()

    assert len(fake_provider.embed_many_calls) == 1
    texts, with_batching = fake_provider.embed_many_calls[0]
    assert with_batching is True
    assert pending_scenes[0].title in texts[0]
    assert pending_scenes[0].description in texts[0]
    assert pending_scenes[0].questions_raised[0] in texts[0]
    assert pending_scenes[0].tags[0] in texts[0]
    assert pending_scenes[0].mentioned_entities[0] in texts[0]


async def test_current_embeddings_are_not_regenerated(
    embedding_service: EmbeddingService,
    current_scene: SceneRow,
    fake_provider: FakeAIProvider,
    fake_scene_repo: FakeSceneRepository,
) -> None:
    await embedding_service.embed_pending_batched()

    stored = fake_scene_repo.get(current_scene.id)
    assert stored is not None
    assert fake_provider.call_count == 0
    assert fake_scene_repo.embedding_updates == []
    assert stored.embedded_at == current_scene.embedded_at


async def test_pending_query_respects_configured_batch_size(
    embedding_service: EmbeddingService,
    pending_scenes: list[SceneRow],
    fake_scene_repo: FakeSceneRepository,
) -> None:
    await embedding_service.embed_pending_batched()

    assert fake_scene_repo.pending_limit == config.ai.embedding_batch_size


async def test_embed_scenes_targets_only_requested_chapter(
    embedding_service: EmbeddingService,
    pending_scenes: list[SceneRow],
    current_scene: SceneRow,
    fake_scene_repo: FakeSceneRepository,
) -> None:
    await embedding_service.embed_scenes("chapter-1")

    updated_ids = [scene_id for scene_id, _, _ in fake_scene_repo.embedding_updates]
    assert updated_ids == [scene.id for scene in pending_scenes]
    assert current_scene.id not in updated_ids
