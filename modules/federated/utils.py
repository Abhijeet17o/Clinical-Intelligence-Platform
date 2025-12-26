"""
Federated Learning Utilities

Helper functions for error handling, retry logic, and other utilities.
"""

import logging
import time
from typing import Callable, Optional, TypeVar, Any
from functools import wraps
import hashlib
import secrets

logger = logging.getLogger(__name__)

T = TypeVar('T')


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Retry decorator for functions that may fail.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry on
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay:.1f}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
            
            raise last_exception
        
        return wrapper
    return decorator


def safe_execute(
    func: Callable[..., T],
    default: Optional[T] = None,
    log_error: bool = True
) -> Optional[T]:
    """
    Safely execute a function, returning default value on error.
    
    Args:
        func: Function to execute
        default: Default value to return on error
        log_error: Whether to log errors
    
    Returns:
        Function result or default value
    """
    try:
        return func()
    except Exception as e:
        if log_error:
            logger.error(f"Error in safe_execute: {e}", exc_info=True)
        return default


def generate_auth_token(length: int = 32) -> str:
    """
    Generate a secure authentication token.
    
    Args:
        length: Token length in bytes
    
    Returns:
        Hex-encoded token string
    """
    return secrets.token_hex(length)


def hash_model_weights(weights: list) -> str:
    """
    Generate hash of model weights for verification.
    
    Args:
        weights: List of weight arrays
    
    Returns:
        SHA256 hash string
    """
    import numpy as np
    
    # Concatenate all weights into single array
    combined = np.concatenate([w.flatten() for w in weights])
    
    # Generate hash
    hash_obj = hashlib.sha256(combined.tobytes())
    return hash_obj.hexdigest()


def validate_client_token(token: str, expected_token: Optional[str]) -> bool:
    """
    Validate client authentication token.
    
    Args:
        token: Token to validate
        expected_token: Expected token value
    
    Returns:
        True if token is valid
    """
    if expected_token is None:
        return True  # No authentication required
    
    return secrets.compare_digest(token, expected_token)


class GracefulDegradation:
    """
    Context manager for graceful degradation when errors occur.
    """
    
    def __init__(self, fallback_value: Any = None, log_errors: bool = True):
        """
        Initialize graceful degradation context.
        
        Args:
            fallback_value: Value to return on error
            log_errors: Whether to log errors
        """
        self.fallback_value = fallback_value
        self.log_errors = log_errors
        self.error_occurred = False
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.error_occurred = True
            if self.log_errors:
                logger.warning(f"Graceful degradation: {exc_val}")
            return True  # Suppress exception
    
    def execute(self, func: Callable[..., T], *args, **kwargs) -> Optional[T]:
        """
        Execute function with graceful degradation.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Function result or fallback value
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.error_occurred = True
            if self.log_errors:
                logger.warning(f"Graceful degradation in {func.__name__}: {e}")
            return self.fallback_value

