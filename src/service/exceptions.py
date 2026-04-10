class ServiceError(Exception):
    code: str = "SERVICE_ERROR"
    status_code: int = 400

    def __init__(self, message: str = "Service error"):
        self.message = message
        super().__init__(message)


class AuthError(ServiceError):
    code = "UNAUTHORIZED"
    status_code = 401

    def __init__(self, message: str = "Authentication required"):
        super().__init__(message)


class ForbiddenError(ServiceError):
    code = "FORBIDDEN"
    status_code = 403

    def __init__(self, message: str = "Access denied"):
        super().__init__(message)


class NotFoundError(ServiceError):
    code = "NOT_FOUND"
    status_code = 404

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message)


class ConflictError(ServiceError):
    code = "CONFLICT"
    status_code = 409

    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message)


class ValidationError(ServiceError):
    code = "VALIDATION_ERROR"
    status_code = 422

    def __init__(self, fields: dict | None = None, message: str = "Validation failed"):
        self.fields = fields or {}
        super().__init__(message)


class RateLimitError(ServiceError):
    code = "RATE_LIMITED"
    status_code = 429

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message)


class InternalError(ServiceError):
    code = "INTERNAL_ERROR"
    status_code = 500

    def __init__(self, message: str = "Internal error"):
        super().__init__(message)
