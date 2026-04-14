from functools import wraps
from src.shared.utils.logging_context import get_layer_logger, LAYER_SHARED
from typing import Callable, ParamSpec, TypeVar, overload, Awaitable
import inspect

log = get_layer_logger(LAYER_SHARED)

P = ParamSpec("P")
T = TypeVar("T")


@overload
def log_errors(func: Callable[P, T]) -> Callable[P, T]: ...


@overload
def log_errors(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]: ...


def log_errors(func):
    """Log exceptions from sync or async functions before re-raising."""

    if inspect.iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except Exception:
                log.exception(f"{func.__name__} failed")
                raise

        return async_wrapper

    else:

        @wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except Exception:
                log.exception(f"{func.__name__} failed")
                raise

        return sync_wrapper


def singleton(cls):
    """
    A singleton decorator. Returns a wrapper object.
    A call on that object returns a single instance of the decorated class.
    """
    _instances = {}

    def wrapper(*args, **kwargs):
        if cls not in _instances:
            _instances[cls] = cls(*args, **kwargs)
        return _instances[cls]

    return wrapper
