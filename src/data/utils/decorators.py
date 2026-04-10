import functools
import re

from src.data.exceptions import DataError, DuplicateError, DataIntegrityError


def handle_data_errors(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except DataError:
            raise
        except Exception as e:
            error_str = str(e).lower()
            if "unique" in error_str or "duplicate" in error_str:
                field = _extract_field(str(e))
                raise DuplicateError(func.__qualname__, field)
            raise DataIntegrityError(str(e))

    return wrapper


def _extract_field(error_msg: str) -> str:
    match = re.search(r"_(\w+)_key", error_msg)
    return match.group(1) if match else "field"
