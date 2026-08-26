class FakeQueue:
    def __init__(self):
        self.enqueued: list[tuple[str, dict]] = []
        self.error: Exception | None = None

    async def enqueue(self, job_name: str, **kwargs):
        if self.error:
            raise self.error
        self.enqueued.append((job_name, kwargs))
