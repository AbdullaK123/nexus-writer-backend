class FakeTransaction:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class FakeConnection:
    def transaction(self):
        return FakeTransaction()

    async def execute(self, *_args, **_kwargs):
        return None


class FakePoolContext:
    async def __aenter__(self):
        return FakeConnection()

    async def __aexit__(self, *args):
        pass


class FakePool:
    def acquire(self):
        return FakePoolContext()
