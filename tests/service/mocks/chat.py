class FakeChatRepository:
    def __init__(self):
        self._threads: dict[str, dict] = {}
        self._messages: dict[str, list[dict]] = {}
        self.error: Exception | None = None

    async def create_thread(
        self,
        *,
        thread_id: str,
        user_id: str,
        story_id: str,
        title: str,
    ) -> dict:
        if self.error:
            raise self.error
        thread = {
            "id": thread_id,
            "user_id": user_id,
            "story_id": story_id,
            "title": title,
        }
        self._threads[thread_id] = thread
        self._messages[thread_id] = []
        return thread

    async def get_thread(self, thread_id: str, user_id: str) -> dict | None:
        if self.error:
            raise self.error
        thread = self._threads.get(thread_id)
        if thread and thread["user_id"] == user_id:
            return thread
        return None

    async def list_threads_for_story(self, story_id: str, user_id: str) -> list[dict]:
        if self.error:
            raise self.error
        return [
            thread
            for thread in self._threads.values()
            if thread["story_id"] == story_id and thread["user_id"] == user_id
        ]

    async def update_thread_title(
        self,
        thread_id: str,
        user_id: str,
        title: str,
    ) -> dict | None:
        if self.error:
            raise self.error
        thread = await self.get_thread(thread_id, user_id)
        if thread:
            thread["title"] = title
        return thread

    async def touch_thread(self, thread_id: str) -> None:
        if self.error:
            raise self.error

    async def delete_thread(self, thread_id: str, user_id: str) -> bool:
        if self.error:
            raise self.error
        thread = self._threads.get(thread_id)
        if thread and thread["user_id"] == user_id:
            del self._threads[thread_id]
            return True
        return False

    async def append_message(self, **kwargs) -> dict:
        if self.error:
            raise self.error
        thread_id = kwargs.get("thread_id", "")
        message = kwargs
        if thread_id in self._messages:
            self._messages[thread_id].append(message)
        return message

    async def list_messages(self, thread_id: str, user_id: str) -> list[dict]:
        if self.error:
            raise self.error
        return self._messages.get(thread_id, [])
