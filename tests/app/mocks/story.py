from typing import Any


class StubStoryService:
    def __init__(self) -> None:
        self.get_story_details_result: Any = None
        self.error: Exception | None = None

    async def get_story_details(self, user_id: str, story_id: str) -> Any:
        if self.error:
            raise self.error
        return self.get_story_details_result
