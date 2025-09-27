"""
Rate limiting and retry utilities.
"""
import time
import logging
import random
from typing import Callable, Any, Optional, Dict
from functools import wraps
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter with token bucket algorithm."""
    
    def __init__(self, max_requests: int, time_window: float):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed in time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
    
    def acquire(self) -> bool:
        """
        Try to acquire permission to make a request.
        
        Returns:
            True if request is allowed, False otherwise
        """
        now = time.time()
        
        # Remove old requests outside time window
        self.requests = [req_time for req_time in self.requests 
                        if now - req_time < self.time_window]
        
        # Check if we can make a new request
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        
        return False
    
    def wait_time(self) -> float:
        """
        Calculate time to wait before next request is allowed.
        
        Returns:
            Time to wait in seconds
        """
        if not self.requests:
            return 0.0
        
        oldest_request = min(self.requests)
        wait_time = self.time_window - (time.time() - oldest_request)
        return max(0.0, wait_time)


def rate_limit(max_requests: int, time_window: float):
    """
    Decorator to rate limit function calls.
    
    Args:
        max_requests: Maximum requests allowed in time window
        time_window: Time window in seconds
    """
    limiter = RateLimiter(max_requests, time_window)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Wait if necessary
            if not limiter.acquire():
                wait_time = limiter.wait_time()
                logger.info(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                time.sleep(wait_time)
                limiter.acquire()  # Try again
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def polite_delay(min_delay: float = 1.0, max_delay: float = 3.0):
    """
    Add random delay between requests to be polite.
    
    Args:
        min_delay: Minimum delay in seconds
        max_delay: Maximum delay in seconds
    """
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)


def retry_with_backoff(max_attempts: int = 3, base_delay: float = 1.0, 
                      max_delay: float = 60.0, exponential_base: float = 2.0):
    """
    Decorator for retrying with exponential backoff.
    
    Args:
        max_attempts: Maximum number of attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        logger.error(f"Function {func.__name__} failed after {max_attempts} attempts: {e}")
                        raise e
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    # Add jitter to avoid thundering herd
                    jitter = random.uniform(0.1, 0.3) * delay
                    total_delay = delay + jitter
                    
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                                 f"Retrying in {total_delay:.2f} seconds...")
                    time.sleep(total_delay)
            
            raise last_exception
        return wrapper
    return decorator


def check_robots_txt(url: str, user_agent: str = "supply-chain-risk-analysis") -> bool:
    """
    Check if URL is allowed by robots.txt.
    
    Args:
        url: URL to check
        user_agent: User agent string
        
    Returns:
        True if allowed, False otherwise
    """
    try:
        from urllib.parse import urljoin, urlparse
        import urllib.robotparser
        
        parsed_url = urlparse(url)
        robots_url = urljoin(url, '/robots.txt')
        
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        
        return rp.can_fetch(user_agent, url)
    except Exception as e:
        logger.warning(f"Could not check robots.txt for {url}: {e}")
        return True  # Assume allowed if check fails


class APIClient:
    """Base API client with rate limiting and retry logic."""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None,
                 rate_limit_requests: int = 100, rate_limit_window: float = 3600.0,
                 max_retries: int = 3):
        """
        Initialize API client.
        
        Args:
            base_url: Base URL for API
            api_key: API key for authentication
            rate_limit_requests: Max requests per time window
            rate_limit_window: Time window in seconds
            max_retries: Maximum retry attempts
        """
        self.base_url = base_url
        self.api_key = api_key
        self.rate_limiter = RateLimiter(rate_limit_requests, rate_limit_window)
        self.max_retries = max_retries
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})
    
    @retry_with_backoff(max_attempts=3)
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, 
            timeout: int = 30) -> requests.Response:
        """
        Make GET request with rate limiting and retry logic.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            timeout: Request timeout
            
        Returns:
            Response object
        """
        # Rate limiting
        if not self.rate_limiter.acquire():
            wait_time = self.rate_limiter.wait_time()
            logger.info(f"Rate limit reached, waiting {wait_time:.2f} seconds")
            time.sleep(wait_time)
            self.rate_limiter.acquire()
        
        # Add polite delay
        polite_delay(0.5, 1.5)
        
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
    
    @retry_with_backoff(max_attempts=3)
    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None,
             json_data: Optional[Dict[str, Any]] = None, timeout: int = 30) -> requests.Response:
        """
        Make POST request with rate limiting and retry logic.
        
        Args:
            endpoint: API endpoint
            data: Form data
            json_data: JSON data
            timeout: Request timeout
            
        Returns:
            Response object
        """
        # Rate limiting
        if not self.rate_limiter.acquire():
            wait_time = self.rate_limiter.wait_time()
            logger.info(f"Rate limit reached, waiting {wait_time:.2f} seconds")
            time.sleep(wait_time)
            self.rate_limiter.acquire()
        
        # Add polite delay
        polite_delay(0.5, 1.5)
        
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.post(url, data=data, json=json_data, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise


# Tenacity-based retry decorators for specific use cases
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((requests.exceptions.RequestException, ConnectionError))
)
def robust_request(func: Callable) -> Callable:
    """
    Decorator for robust HTTP requests using tenacity.
    """
    return func


def safe_request(url: str, method: str = 'GET', **kwargs) -> Optional[requests.Response]:
    """
    Make a safe HTTP request with error handling.
    
    Args:
        url: URL to request
        method: HTTP method
        **kwargs: Additional arguments for requests
        
    Returns:
        Response object or None if failed
    """
    try:
        response = requests.request(method, url, timeout=30, **kwargs)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        logger.warning(f"Request failed for {url}: {e}")
        return None


def batch_process(items: list, batch_size: int, delay_between_batches: float = 1.0):
    """
    Process items in batches with delays.
    
    Args:
        items: List of items to process
        batch_size: Size of each batch
        delay_between_batches: Delay between batches in seconds
        
    Yields:
        Batches of items
    """
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        yield batch
        
        # Add delay between batches (except for the last one)
        if i + batch_size < len(items):
            time.sleep(delay_between_batches)

