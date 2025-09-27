"""
Rate limiting and throttling utilities for API calls and data collection.
"""
import time
import asyncio
from typing import Dict, Optional, Callable, Any
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for API calls and data collection."""
    
    def __init__(self, max_calls: int, time_window: int):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = deque()
        self.lock = asyncio.Lock()
    
    async def acquire(self) -> bool:
        """Acquire permission to make a call."""
        async with self.lock:
            now = time.time()
            
            # Remove old calls outside the time window
            while self.calls and self.calls[0] <= now - self.time_window:
                self.calls.popleft()
            
            # Check if we can make another call
            if len(self.calls) < self.max_calls:
                self.calls.append(now)
                return True
            
            return False
    
    async def wait_for_slot(self) -> None:
        """Wait until a slot becomes available."""
        while not await self.acquire():
            if self.calls:
                wait_time = self.calls[0] + self.time_window - time.time()
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
            else:
                await asyncio.sleep(0.1)


class APIRateLimiter:
    """Rate limiter specifically for API services."""
    
    def __init__(self):
        self.limiters: Dict[str, RateLimiter] = {}
        self._setup_default_limits()
    
    def _setup_default_limits(self):
        """Setup default rate limits for common APIs."""
        self.limiters['serp'] = RateLimiter(100, 3600)  # 100 requests per hour
        self.limiters['twitter'] = RateLimiter(300, 900)  # 300 requests per 15 minutes
        self.limiters['weather'] = RateLimiter(1000, 3600)  # 1000 requests per hour
        self.limiters['rss'] = RateLimiter(600, 3600)  # 600 requests per hour
        self.limiters['crawl'] = RateLimiter(300, 3600)  # 300 requests per hour
    
    async def wait_for_api_call(self, service: str) -> None:
        """Wait for permission to make an API call."""
        if service in self.limiters:
            await self.limiters[service].wait_for_slot()
    
    async def can_make_call(self, service: str) -> bool:
        """Check if we can make an API call immediately."""
        if service in self.limiters:
            return await self.limiters[service].acquire()
        return True


class RetryWithBackoff:
    """Retry mechanism with exponential backoff."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, 
                 max_delay: float = 60.0, exponential_base: float = 2.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
    
    async def __call__(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic."""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    logger.error(f"Function {func.__name__} failed after {self.max_retries} retries: {e}")
                    raise e
                
                # Calculate delay with exponential backoff
                delay = min(
                    self.base_delay * (self.exponential_base ** attempt),
                    self.max_delay
                )
                
                logger.warning(f"Function {func.__name__} failed (attempt {attempt + 1}), retrying in {delay:.2f}s: {e}")
                await asyncio.sleep(delay)
        
        raise last_exception


# Global rate limit manager
api_rate_limiter = APIRateLimiter()
retry_handler = RetryWithBackoff()