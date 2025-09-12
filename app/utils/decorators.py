from functools import wraps
from loguru import logger
from typing import Callable, ParamSpec, TypeVar
from app.workers import AsyncBackgroundWorker

P = ParamSpec('P')
T = TypeVar('T')


def log_errors(func: Callable[P, T]) -> Callable[P, T]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"{func.__name__} failed with an exception: \n {e}")
            raise e
    return wrapper