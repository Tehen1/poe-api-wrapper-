import time
from random import uniform
from typing import Optional, Dict
from threading import Lock

class RateLimitHandler:
    """Handles rate limiting with exponential backoff."""
    def __init__(self):
        self.base_wait = 2.0  # Base wait time in seconds
        self.max_wait = 60.0  # Maximum wait time in seconds
        self.backoff_factor = 2.0  # Multiplier for exponential backoff
        self.max_retries = 5
        self._window_start: Dict[str, float] = {}  # Track rate limit windows per endpoint
        self._attempt_counts: Dict[str, int] = {}  # Track retry attempts
        self._lock = Lock()
    
    def should_retry(self, endpoint: str) -> bool:
        """Check if we should retry a rate-limited request."""
        with self._lock:
            attempts = self._attempt_counts.get(endpoint, 0)
            return attempts < self.max_retries
    
    def get_retry_after(self, endpoint: str) -> float:
        """Calculate wait time with exponential backoff."""
        with self._lock:
            attempts = self._attempt_counts.get(endpoint, 0)
            wait_time = min(
                self.base_wait * (self.backoff_factor ** attempts),
                self.max_wait
            )
            # Add jitter to prevent thundering herd
            jitter = uniform(-0.1, 0.1) * wait_time
            return wait_time + jitter
    
    def record_attempt(self, endpoint: str):
        """Record a rate limit hit for an endpoint."""
        with self._lock:
            self._attempt_counts[endpoint] = self._attempt_counts.get(endpoint, 0) + 1
    
    def reset_attempts(self, endpoint: str):
        """Reset attempt counter after successful request."""
        with self._lock:
            if endpoint in self._attempt_counts:
                del self._attempt_counts[endpoint]
    
    def update_window(self, endpoint: str):
        """Update rate limit window start time."""
        with self._lock:
            self._window_start[endpoint] = time.time()
    
    def get_window_remaining(self, endpoint: str) -> Optional[float]:
        """Get remaining time in current rate limit window."""
        with self._lock:
            if endpoint in self._window_start:
                elapsed = time.time() - self._window_start[endpoint]
                if elapsed < self.base_wait:
                    return self.base_wait - elapsed
        return None

