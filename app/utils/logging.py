from loguru import logger
import time
from typing import Callable, Any
import functools


# decorator to log background job
def log_background_job(func: Callable):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        
        job_name = func.__name__
        start_time = time.perf_counter()

        logger.info(
            "🚀 Starting background job: {job_name}",
            job_name=job_name,
            args=str(args)[:200],  # Truncate long arguments
            kwargs={k: str(v)[:100] for k, v in kwargs.items()},  # Truncate long values
            start_time=start_time,
            job_type="background_task"
        )

        try:

            result = await func(*args, **kwargs)

            # Calculate execution time
            duration = time.perf_counter() - start_time
            
            # Log successful completion with metrics
            logger.success(
                "✅ Background job completed: {job_name} in {duration}s",
                job_name=job_name,
                duration=round(duration, 3),
                status="success",
                result_type=type(result).__name__ if result is not None else "None",
                job_type="background_task"
            )
            
            return result
        
        except Exception as e:

            duration = time.perf_counter() - start_time

             # Log failure with comprehensive error context
            logger.error(
                "❌ Background job failed: {job_name} after {duration}s - {error_type}: {error_msg}",
                job_name=job_name,
                duration=round(duration, 3),
                status="failed",
                error_type=type(e).__name__,
                error_msg=str(e),
                error_args=str(e.args) if e.args else None,
                job_type="background_task",
                args=str(args)[:200]
            )
            
            # Re-raise the exception so retry logic can handle it
            raise

    return wrapper



# decorator to log the performance of a background job
def log_performance(threshold: float = 5.0):
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            
            func_name = func.__name__
            start_time = time.perf_counter()

            try:

                result = await func(*args, *kwargs)
                execution_time = time.perf_counter() - start_time

                if execution_time > threshold:
                    # warn about slow performance
                    logger.warning(
                        "🐌 Slow operation detected: {function} took {duration}s (threshold: {threshold}s)",
                        function=func_name,
                        duration=round(execution_time, 3),
                        threshold=threshold,
                        performance_issue=True,
                        args=str(args)[:100]
                    )
                else:
                    # log the performance
                    logger.debug(
                        "⚡ {function} completed in {duration}s",
                        function=func_name,
                        duration=round(execution_time, 3),
                        performance_ok=True
                    )

                return result

            except Exception as e:
                execution_time = time.perf_counter() - start_time

                duration = time.time() - start_time
                
                logger.error(
                    "💥 Function {function} failed after {duration}s: {error_type} - {error_msg}",
                    function=func_name,
                    duration=round(duration, 3),
                    error_type=type(e).__name__,
                    error_msg=str(e),
                    performance_failure=True,
                    args=str(args)[:100]
                )

                raise

        return wrapper
    return decorator



# decorator to log database operations
def log_database_operation(operation_type: str = "unknown"):
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            
            logger.debug(
                "🗄️ Starting database operation: {operation_type} in {function}",
                operation_type=operation_type,
                function=func.__name__,
                args=str(args)[:100]
            )
            
            try:
                result = await func(*args, **kwargs)
                duration = time.perf_counter() - start_time
                
                logger.debug(
                    "✅ Database operation completed: {operation_type} in {duration}s",
                    operation_type=operation_type,
                    function=func.__name__,
                    duration=round(duration, 3),
                    db_operation=True
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                logger.error(
                    "❌ Database operation failed: {operation_type} after {duration}s - {error_type}: {error_msg}",
                    operation_type=operation_type,
                    function=func.__name__,
                    duration=round(duration, 3),
                    error_type=type(e).__name__,
                    error_msg=str(e),
                    db_operation=True,
                    db_error=True
                )
                raise
                
        return wrapper
    return decorator