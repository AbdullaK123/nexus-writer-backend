from functools import wraps
from loguru import logger
from typing import Callable, ParamSpec, TypeVar, overload, Awaitable
import inspect

P = ParamSpec('P')
T = TypeVar('T')


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
                logger.exception(f"{func.__name__} failed")
                raise
        return async_wrapper
    
    else:
        @wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except Exception:
                logger.exception(f"{func.__name__} failed")
                raise
        return sync_wrapper
    


def singleton(cls):
    """
    A singleton decorator. Returns a wrapper object.
    A call on that object returns a single instance of the decorated class.
    """
    _instances = {}  # Dictionary to store instances of decorated classes

    def wrapper(*args, **kwargs):
        """Returns a single instance of decorated class"""
        if cls not in _instances:
            # Create a new instance if it doesn't exist and store it
            _instances[cls] = cls(*args, **kwargs)
        # Always return the stored instance
        return _instances[cls]

    return wrapper
