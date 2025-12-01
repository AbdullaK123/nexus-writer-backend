from loguru import logger
import sys
from pathlib import Path
from app.utils.logging_context import get_correlation_id, get_user_id

def setup_logging():
    """Configure Loguru for comprehensive application logging"""
    
    # Remove default handler
    logger.remove()
    
    # Console logging with beautiful colors and emojis
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True,
        enqueue=True  # Thread-safe
    )
    
    # Comprehensive background job logging with JSON structure
    logger.add(
        "logs/celery_tasks.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="25 MB",  # Larger files for background jobs
        retention="30 days",
        compression="zip",
        serialize=True,  # JSON format for structured logging
        enqueue=True,
        filter=lambda record: record["extra"].get("job_type") == "background_task"
    )
    
    # Retry attempts and error recovery logging
    logger.add(
        "logs/retry_attempts.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level="WARNING",
        rotation="10 MB",
        retention="15 days",
        compression="zip",
        serialize=True,
        enqueue=True,
        filter=lambda record: any(keyword in record["message"].lower() 
                                for keyword in ["retry", "failed", "attempt"])
    )
    
    # Performance monitoring logs
    logger.add(
        "logs/performance.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level="WARNING",
        rotation="15 MB",
        retention="7 days",
        compression="zip",
        serialize=True,
        enqueue=True,
        filter=lambda record: record["extra"].get("performance_issue") or record["extra"].get("performance_failure")
    )
    
    # Database operation logs
    logger.add(
        "logs/database.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="20 MB",
        retention="14 days",
        compression="zip",
        serialize=True,
        enqueue=True,
        filter=lambda record: record["extra"].get("db_operation")
    )

    # HTTP request/response logs
    logger.add(
        "logs/http.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}",
        level="INFO",
        rotation="50 MB",
        retention="30 days",
        compression="zip",
        serialize=True,  # JSON for easy ingestion
        enqueue=True,
        filter=lambda record: record["extra"].get("http") is True
    )
    
    # Critical errors only
    logger.add(
        "logs/errors.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="10 MB",
        retention="60 days",  # Keep errors longer
        compression="zip",
        serialize=True,
        enqueue=True
    )
    
    logger.success("🎯 Enhanced Loguru logging system initialized with structured output")

# Ensure logs directory exists
Path("logs").mkdir(exist_ok=True)