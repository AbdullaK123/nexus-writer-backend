import pytest

from src.data.schemas.scene import SceneRow
from src.service.embedding.service import EmbeddingService
from tests.service.mocks import FakeAIProvider, FakeSceneRepository


async def test_provider_failure_does_not_mark_scenes_current(
    embedding_service: EmbeddingService,
    pending_scenes: list[SceneRow],
    fake_provider: FakeAIProvider,
    fake_scene_repo: FakeSceneRepository,
) -> None:
    fake_provider.error = RuntimeError("embedding provider unavailable")

    with pytest.raises(RuntimeError, match="embedding provider unavailable"):
        await embedding_service.embed_pending_batched()

    assert fake_scene_repo.embedding_updates == []
    assert all(fake_scene_repo.get(scene.id).embedded_at is None for scene in pending_scenes)


async def test_persistence_failure_leaves_failed_scene_pending_and_continues_batch(
    embedding_service: EmbeddingService,
    pending_scenes: list[SceneRow],
    fake_scene_repo: FakeSceneRepository,
) -> None:
    failed_scene, successful_scene = pending_scenes
    fake_scene_repo.update_embedding_errors[failed_scene.id] = RuntimeError("db write failed")

    await embedding_service.embed_pending_batched()

    failed = fake_scene_repo.get(failed_scene.id)
    successful = fake_scene_repo.get(successful_scene.id)
    assert failed is not None
    assert successful is not None
    assert failed.embedded_at is None
    assert successful.embedded_at is not None
    assert [scene_id for scene_id, _, _ in fake_scene_repo.embedding_updates] == [
        successful_scene.id
    ]
