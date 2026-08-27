class FakeHeartbeatPath:
    def __init__(self) -> None:
        self.touch_count = 0

    def touch(self) -> None:
        self.touch_count += 1


class FakeSessionCleanupService:
    def __init__(self) -> None:
        self.calls = 0
        self.error: Exception | None = None

    async def cleanup_expired_sessions(self) -> None:
        self.calls += 1
        if self.error:
            raise self.error


class FakeReextractionService:
    def __init__(self) -> None:
        self.calls = 0
        self.error: Exception | None = None

    async def regenerate_stale_batched(self) -> None:
        self.calls += 1
        if self.error:
            raise self.error


class FakeCronEmbeddingService:
    def __init__(self) -> None:
        self.calls = 0
        self.error: Exception | None = None

    async def embed_pending_batched(self) -> None:
        self.calls += 1
        if self.error:
            raise self.error
