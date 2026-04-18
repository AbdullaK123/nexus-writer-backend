

class InfrastructureError(Exception):
    pass


class DatabaseError(InfrastructureError):
    def __init__(self, message: str, original: Exception | None = None):
        self.original = original
        super().__init__(message)

class LLMConfigError(InfrastructureError):
    def __init__(self, message: str, original: Exception | None = None):
        self.original = original
        super().__init__(message)

class LLMServiceError(InfrastructureError):
    def __init__(self, message: str, original: Exception | None = None):
        self.original = original
        super().__init__(message)