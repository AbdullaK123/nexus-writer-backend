import asyncio
import functools
from typing import Callable, Type, Tuple
from sqlalchemy.exc import OperationalError, IntegrityError
from loguru import logger

def async_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    retry_on: Tuple[Type[Exception], ...] = (Exception,),
    no_retry_on: Tuple[Type[Exception], ...] = ()
):
    """
    Decorator that adds retry logic to async functions with clean exception handling
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            
            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        logger.debug(
                            "🔄 Retry attempt {attempt} for {function}",
                            attempt=attempt,
                            function=func.__name__
                        )
                    
                    return await func(*args, **kwargs)
                    
                except no_retry_on as e:
                    # Don't retry these exceptions - immediate failure
                    logger.warning(
                        "🚫 No retry for {function}: {error_type} - {error_msg} (permanent failure)",
                        function=func.__name__,
                        error_type=type(e).__name__,
                        error_msg=str(e)
                    )
                    raise  # Re-raise the original exception immediately
                    
                except retry_on as e:
                    # This is the current exception for this attempt
                    
                    if attempt == max_retries:
                        # Final attempt failed - re-raise the current exception
                        logger.error(
                            "💀 Final retry failed for {function}: {error_type} - {error_msg}",
                            function=func.__name__,
                            error_type=type(e).__name__,
                            error_msg=str(e),
                            total_attempts=attempt + 1,
                            max_retries=max_retries
                        )
                        raise  # Re-raise the current exception
                    
                    # Not the final attempt - log and continue
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    
                    logger.warning(
                        "⚠️ Retry {attempt}/{max_retries} for {function}: {error_type} - {error_msg}. Waiting {delay}s...",
                        function=func.__name__,
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        error_type=type(e).__name__,
                        error_msg=str(e),
                        delay=delay
                    )
                    
                    await asyncio.sleep(delay)

            raise RuntimeError(f"Unexpected state in retry logic for {func.__name__}")
            
        return wrapper
    return decorator


def db_retry(max_retries: int = 3):
    """Specialized retry decorator for database operations"""
    return async_retry(
        max_retries=max_retries,
        base_delay=1.0,
        max_delay=10.0,
        retry_on=(OperationalError, ConnectionError, TimeoutError),
        no_retry_on=(IntegrityError, ValueError)
    )