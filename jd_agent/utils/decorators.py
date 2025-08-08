"""
Decorators for the JD Agent application.
"""

import time
import functools
from typing import Any, Callable, TypeVar

from .logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


def log_time(event_name: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to log function execution time.
    
    Args:
        event_name: Name of the event to log
        
    Returns:
        Callable: Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed_ms = int((time.perf_counter() - start_time) * 1000)
                
                # Log success
                logger.info(
                    event_name,
                    status="success",
                    elapsed_ms=elapsed_ms,
                    func_name=func.__name__
                )
                
                return result
            except Exception as e:
                elapsed_ms = int((time.perf_counter() - start_time) * 1000)
                
                # Log error
                logger.error(
                    event_name,
                    status="error",
                    elapsed_ms=elapsed_ms,
                    func_name=func.__name__,
                    error=str(e)
                )
                raise
        
        return wrapper
    return decorator


def log_time_async(event_name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator to log async function execution time.
    
    Args:
        event_name: Name of the event to log
        
    Returns:
        Callable: Decorated async function
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                elapsed_ms = int((time.perf_counter() - start_time) * 1000)
                
                # Log success
                logger.info(
                    event_name,
                    status="success",
                    elapsed_ms=elapsed_ms,
                    func_name=func.__name__
                )
                
                return result
            except Exception as e:
                elapsed_ms = int((time.perf_counter() - start_time) * 1000)
                
                # Log error
                logger.error(
                    event_name,
                    status="error",
                    elapsed_ms=elapsed_ms,
                    func_name=func.__name__,
                    error=str(e)
                )
                raise
        
        return wrapper
    return decorator 


def timing_decorator(func: Callable[..., T]) -> Callable[..., T]:
    """Simple timing decorator expected by tests.

    Measures execution time of a sync function and logs it.
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        start_time = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            logger.info("function_timing", func_name=func.__name__, elapsed_ms=elapsed_ms)

    return wrapper