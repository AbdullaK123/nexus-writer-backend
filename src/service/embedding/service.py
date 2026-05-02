
from typing import List
from src.data.repositories.scene import SceneRepository
from src.data.schemas.scene import SceneRow
from src.infrastructure.ai.providers.protocol import AIProvider
from src.infrastructure.config import config
from src.service.exceptions import ServiceError
from loguru import logger


class EmbeddingService:

    def __init__(
        self,
        scene_repo: SceneRepository,
        provider: AIProvider
    ) -> None:
        self._scene_repo = scene_repo
        self._provider = provider


    def _format_scene(self, row: SceneRow) -> str:
        return f"""
        {row.title}\n\n
        {row.description}\n\n
        {" ".join(row.questions_raised)}\n\n
        {" ".join(row.tags)}
        """


    async def embed_pending_batched(self) -> None:

        # grab scenes with no embeddings
        scenes_to_embed: List[SceneRow] = await self._scene_repo.list_pending_embeddings(limit=config.ai.embedding_batch_size)

        if not scenes_to_embed:
            return

        logger.info(
            "embed_pending_batched.start",
            batch_size=len(scenes_to_embed),
            embedding_model=self._provider.embedding_model,
        )

        # grab text to embed and embed them
        texts = [self._format_scene(scene) for scene in scenes_to_embed]
        
        embeddings = await self._provider.embed_many(texts, with_batching=True)

        if len(embeddings) != len(scenes_to_embed):
            logger.error(
                "embed_pending_batched.malformed_response",
                requested=len(scenes_to_embed),
                received=len(embeddings),
            )
            raise ServiceError("AI provider returned malformed embedding batch.")

        # update embeddings
        updated = 0
        for scene, embedding in zip(scenes_to_embed, embeddings):
            try:
                await self._scene_repo.update_embedding(
                    scene_id=scene.id, 
                    embedding=embedding,
                    embedding_model=self._provider.embedding_model
                )
                updated += 1
            except Exception as e:
                logger.warning(
                    "update_embedding.failed",
                    scene_id=scene.id,
                    error=str(e),
                )

        logger.info(
            "embed_pending_batched.complete",
            scenes_embedded=updated,
            scenes_failed=len(scenes_to_embed) - updated,
        )