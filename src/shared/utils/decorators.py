from functools import wraps
from contextlib import asynccontextmanager
from src.shared.utils.logging_context import get_layer_logger, LAYER_SHARED
from typing import Callable, ParamSpec, TypeVar, overload, Awaitable
import inspect
import time

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
                log.exception("shared.func_failed", func=func.__name__)
                raise

        return async_wrapper

    else:

        @wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except Exception:
                log.exception("shared.func_failed", func=func.__name__)
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


class _TimedContext:
    __slots__ = ("elapsed_s", "_done_kwargs")

    def __init__(self):
        self.elapsed_s: float = 0.0
        self._done_kwargs: dict = {}

    def set(self, **kwargs):
        """Add extra kwargs to the ``.done`` log message."""
        self._done_kwargs.update(kwargs)


@asynccontextmanager
async def timed_event(logger, event: str, *, level: str = "DEBUG", **log_kwargs):
    """Async context manager that logs ``{event}.start``, ``.done``, and
    ``.error`` with ``elapsed_s`` timing.

    *log_kwargs* are forwarded to every log call.  Call :meth:`set` on the
    yielded context to attach result-specific kwargs to the ``.done``
    message only::

        async with timed_event(log, "graph.character.parser",
                               chapter_number=1) as t:
            result = await extractor.extract(prompt)
            t.set(characters_found=len(result.characters))
    """
    ctx = _TimedContext()
    logger.log(level, f"{event}.start", **log_kwargs)
    t0 = time.perf_counter()
    try:
        yield ctx
    except Exception:
        ctx.elapsed_s = round(time.perf_counter() - t0, 2)
        logger.opt(exception=True).error(
            f"{event}.error", elapsed_s=ctx.elapsed_s, **log_kwargs
        )
        raise
    ctx.elapsed_s = round(time.perf_counter() - t0, 2)
    logger.log(
        level, f"{event}.done", elapsed_s=ctx.elapsed_s,
        **log_kwargs, **ctx._done_kwargs
    )
