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