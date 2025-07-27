"""
Retry utilities for handling API calls with exponential backoff.
"""

import asyncio
import functools
import time
from typing import Any, Callable, Optional, TypeVar, Union
from openai import OpenAIError, RateLimitError, APITimeoutError, APIConnectionError

from .logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class MaxRetriesExceededError(Exception):
    """Custom exception raised when maximum retries are exceeded."""
    
    def __init__(self, func_name: str, max_retries: int, last_exception: Exception):
        self.func_name = func_name
        self.max_retries = max_retries
        self.last_exception = last_exception
        super().__init__(
            f"Max retries ({max_retries}) exceeded for {func_name}. "
            f"Last exception: {type(last_exception).__name__}: {last_exception}"
        )


def with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_exceptions: tuple = (RateLimitError, APITimeoutError, APIConnectionError, OpenAIError)
):
    """
    Decorator for retrying function calls with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        exponential_base: Base for exponential backoff calculation
        jitter: Whether to add random jitter to delays
        retry_exceptions: Tuple of exceptions to retry on
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retry_exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}: {e}")
                        raise MaxRetriesExceededError(func.__name__, max_retries, e)
                    
                    delay = _calculate_delay(attempt, base_delay, max_delay, exponential_base, jitter)
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay:.2f}s")
                    logger.info(f"Retry delay: {delay:.2f}s (attempt {attempt + 1}/{max_retries + 1})")
                    time.sleep(delay)
            
            # This should never be reached, but just in case
            raise last_exception
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retry_exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}: {e}")
                        raise MaxRetriesExceededError(func.__name__, max_retries, e)
                    
                    delay = _calculate_delay(attempt, base_delay, max_delay, exponential_base, jitter)
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay:.2f}s")
                    logger.info(f"Retry delay: {delay:.2f}s (attempt {attempt + 1}/{max_retries + 1})")
                    await asyncio.sleep(delay)
            
            # This should never be reached, but just in case
            raise last_exception
        
        # Return the appropriate wrapper based on whether the function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def _calculate_delay(
    attempt: int,
    base_delay: float,
    max_delay: float,
    exponential_base: float,
    jitter: bool
) -> float:
    """
    Calculate delay for exponential backoff with optional jitter.
    
    Args:
        attempt: Current attempt number (0-based)
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential calculation
        jitter: Whether to add random jitter
        
    Returns:
        Delay in seconds
    """
    delay = min(base_delay * (exponential_base ** attempt), max_delay)
    
    if jitter:
        import random
        delay = delay * (0.5 + random.random() * 0.5)  # Add ±50% jitter
    
    return delay


# Convenience decorators for common use cases
def with_openai_backoff(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator specifically for OpenAI API calls with standard retry settings."""
    return with_backoff(
        max_retries=3,
        base_delay=1.0,
        max_delay=30.0,
        exponential_base=2.0,
        jitter=True,
        retry_exceptions=(RateLimitError, APITimeoutError, APIConnectionError, OpenAIError)
    )(func)


def with_gentle_backoff(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator for gentle retries with shorter delays."""
    return with_backoff(
        max_retries=2,
        base_delay=0.5,
        max_delay=10.0,
        exponential_base=1.5,
        jitter=True,
        retry_exceptions=(RateLimitError, APITimeoutError, APIConnectionError, OpenAIError)
    )(func)


def with_aggressive_backoff(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator for aggressive retries with longer delays."""
    return with_backoff(
        max_retries=5,
        base_delay=2.0,
        max_delay=120.0,
        exponential_base=3.0,
        jitter=True,
        retry_exceptions=(RateLimitError, APITimeoutError, APIConnectionError, OpenAIError)
    )(func) 