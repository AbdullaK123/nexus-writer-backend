class InfrastructureError(Exception):
    pass


class DatabaseError(InfrastructureError):
    def __init__(self, message: str, original: Exception | None = None):
        self.original = original
        super().__init__(message)


class RedisError(InfrastructureError):
    def __init__(self, message: str, original: Exception | None = None):
        self.original = original
        super().__init__(message)


class ExternalServiceError(InfrastructureError):
    def __init__(self, message: str, original: Exception | None = None):
        self.original = original
        super().__init__(message)
