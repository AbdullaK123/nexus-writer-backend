class DataError(Exception):
    pass


class NotFoundError(DataError):
    def __init__(self, entity: str, id: str | None = None):
        self.entity = entity
        self.id = id
        super().__init__(f"{entity}{f' {id}' if id else ''} not found")


class DuplicateError(DataError):
    def __init__(self, entity: str, field: str):
        self.entity = entity
        self.field = field
        super().__init__(f"{entity} with this {field} already exists")


class DataIntegrityError(DataError):
    def __init__(self, message: str = "Data integrity violation"):
        super().__init__(message)
