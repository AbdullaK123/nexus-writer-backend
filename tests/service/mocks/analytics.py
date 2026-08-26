class FakeAnalyticsRepository:
    def __init__(self):
        self.error: Exception | None = None

    async def get_cast_statistics(self, story_id: str, user_id: str, *, executor=None) -> list:
        if self.error:
            raise self.error
        return []

    async def get_character_co_occurence_statistics(self, story_id: str, user_id: str, *, executor=None) -> list:
        if self.error:
            raise self.error
        return []

    async def get_character_statistics(self, story_id: str, user_id: str, *, executor=None) -> list:
        if self.error:
            raise self.error
        return []

    async def get_scene_length_distribution(self, story_id: str, user_id: str, *, executor=None) -> list:
        if self.error:
            raise self.error
        return []

    async def get_tension_and_pacing_curves(self, story_id: str, user_id: str, *, executor=None) -> list:
        if self.error:
            raise self.error
        return []

    async def get_recent_chapters_rythm(self, story_id: str, user_id: str, k: int = 5, *, executor=None) -> list:
        if self.error:
            raise self.error
        return []

    async def get_entity_statistics(self, story_id: str, user_id: str, *, executor=None) -> list:
        if self.error:
            raise self.error
        return []

    async def get_questions_raised_by_chapter(self, story_id: str, user_id: str, *, executor=None) -> list:
        if self.error:
            raise self.error
        return []
