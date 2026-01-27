"""
Timing Utilities

Performance timing decorators and utilities.
"""

import time
import functools
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)


def timed(func: Callable) -> Callable:
    """
    Decorator to time function execution.

    Logs execution time at DEBUG level.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = (time.time() - start) * 1000
        logger.debug(f"{func.__name__} took {elapsed:.2f}ms")
        return result
    return wrapper


def timed_async(func: Callable) -> Callable:
    """
    Async decorator to time function execution.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        start = time.time()
        result = await func(*args, **kwargs)
        elapsed = (time.time() - start) * 1000
        logger.debug(f"{func.__name__} took {elapsed:.2f}ms")
        return result
    return wrapper


class Timer:
    """Context manager for timing code blocks."""

    def __init__(self, name: str = "operation"):
        self.name = name
        self.start_time = None
        self.elapsed_ms = 0.0

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, *args):
        self.elapsed_ms = (time.time() - self.start_time) * 1000
        logger.debug(f"{self.name} took {self.elapsed_ms:.2f}ms")

    @property
    def elapsed(self) -> float:
        """Get elapsed time in milliseconds."""
        if self.start_time is None:
            return 0.0
        return (time.time() - self.start_time) * 1000
