from typing import Any


class FakeAnalyticsRepository:
    def __init__(self) -> None:
        self.error: Exception | None = None
        self.cast_statistics: list[tuple[Any, ...]] = []
        self.co_occurrence_statistics: list[tuple[Any, ...]] = []
        self.character_statistics: list[tuple[Any, ...]] = []
        self.scene_length_distribution: list[tuple[Any, ...]] = []
        self.tension_and_pacing_curves: list[tuple[Any, ...]] = []
        self.recent_chapters_rythm: list[tuple[Any, ...]] = []
        self.entity_statistics: list[tuple[Any, ...]] = []
        self.questions_raised: list[tuple[Any, ...]] = []
        self.calls: list[tuple[str, str, str]] = []

    def _record(self, method: str, story_id: str, user_id: str) -> None:
        self.calls.append((method, story_id, user_id))

    async def get_cast_statistics(
        self, story_id: str, user_id: str, *, executor=None
    ) -> list[tuple[Any, ...]]:
        self._record("cast", story_id, user_id)
        if self.error:
            raise self.error
        return list(self.cast_statistics)

    async def get_character_co_occurence_statistics(
        self, story_id: str, user_id: str, *, executor=None
    ) -> list[tuple[Any, ...]]:
        self._record("co_occurrence", story_id, user_id)
        if self.error:
            raise self.error
        return list(self.co_occurrence_statistics)

    async def get_character_statistics(
        self, story_id: str, user_id: str, *, executor=None
    ) -> list[tuple[Any, ...]]:
        self._record("character", story_id, user_id)
        if self.error:
            raise self.error
        return list(self.character_statistics)

    async def get_scene_length_distribution(
        self, story_id: str, user_id: str, *, executor=None
    ) -> list[tuple[Any, ...]]:
        self._record("scene_length", story_id, user_id)
        if self.error:
            raise self.error
        return list(self.scene_length_distribution)

    async def get_tension_and_pacing_curves(
        self, story_id: str, user_id: str, *, executor=None
    ) -> list[tuple[Any, ...]]:
        self._record("curves", story_id, user_id)
        if self.error:
            raise self.error
        return list(self.tension_and_pacing_curves)

    async def get_recent_chapters_rythm(
        self,
        story_id: str,
        user_id: str,
        k: int = 5,
        *,
        executor=None,
    ) -> list[tuple[Any, ...]]:
        self._record("recent_rythm", story_id, user_id)
        if self.error:
            raise self.error
        return list(self.recent_chapters_rythm)

    async def get_entity_statistics(
        self, story_id: str, user_id: str, *, executor=None
    ) -> list[tuple[Any, ...]]:
        self._record("entities", story_id, user_id)
        if self.error:
            raise self.error
        return list(self.entity_statistics)

    async def get_questions_raised_by_chapter(
        self, story_id: str, user_id: str, *, executor=None
    ) -> list[tuple[Any, ...]]:
        self._record("questions", story_id, user_id)
        if self.error:
            raise self.error
        return list(self.questions_raised)
