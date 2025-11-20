"""
Celery worker entry point.
This module is imported by: celery -A app.worker worker
"""
from app.config.celery import celery_app

# Import task modules to register them with Celery
# This ensures Celery discovers all your @celery_app.task decorated functions
from app.workers import *  # or import specific modules

__all__ = ["celery_app"]