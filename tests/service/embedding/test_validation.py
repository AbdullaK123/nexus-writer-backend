import pytest

from src.data.schemas.scene import SceneRow
from src.service.embedding.service import EMBEDDING_DIMENSION, EmbeddingService
from src.service.exceptions import ServiceError
from tests.service.mocks import FakeAIProvider, FakeSceneRepository


async def test_rejects_malformed_batch_length_before_persistence(
    embedding_service: EmbeddingService,
    pending_scenes: list[SceneRow],
    fake_provider: FakeAIProvider,
    fake_scene_repo: FakeSceneRepository,
) -> None:
    fake_provider.embed_many_response = [[0.1] * EMBEDDING_DIMENSION]

    with pytest.raises(ServiceError, match="malformed embedding batch"):
        await embedding_service.embed_pending_batched()

    assert fake_scene_repo.embedding_updates == []


@pytest.mark.parametrize("embedding", [[], [0.1] * 10])
async def test_rejects_invalid_embedding_vectors_before_any_write(
    embedding_service: EmbeddingService,
    pending_scenes: list[SceneRow],
    fake_provider: FakeAIProvider,
    fake_scene_repo: FakeSceneRepository,
    embedding: list[float],
) -> None:
    fake_provider.embed_many_response = [
        embedding,
        [0.2] * EMBEDDING_DIMENSION,
    ]

    with pytest.raises(ServiceError):
        await embedding_service.embed_pending_batched()

    assert fake_scene_repo.embedding_updates == []
