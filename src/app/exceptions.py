class AppError(Exception):
    status_code: int = 400

    def __init__(self, message: str = "Bad request"):
        self.message = message
        super().__init__(message)


class MalformedRequestError(AppError):
    status_code = 400

    def __init__(self, message: str = "Malformed request"):
        super().__init__(message)
