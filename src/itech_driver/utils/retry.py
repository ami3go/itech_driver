"""Retry decorator for unreliable operations."""

import time
from functools import wraps
from typing import Callable, Any, Optional
from ..exceptions import TimeoutError


def retry(
        max_attempts: int = 3,
        delay: float = 0.1,
        backoff: float = 2,
        exceptions: tuple = (Exception,)
):
    """Retry decorator for unreliable operations."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            attempts = 0
            current_delay = delay

            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempts += 1
                    if attempts == max_attempts:
                        raise
                    time.sleep(current_delay)
                    current_delay *= backoff
            return func(*args, **kwargs)

        return wrapper

    return decorator