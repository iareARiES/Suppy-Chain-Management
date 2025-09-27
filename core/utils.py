"""
Utility functions for data processing and manipulation.
"""
import re
import hashlib
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin, urlunparse, parse_qs
import pandas as pd

logger = logging.getLogger(__name__)


def canonicalize_url(url: str) -> str:
    """
    Canonicalize URL by removing tracking parameters and normalizing.
    
    Args:
        url: URL to canonicalize
        
    Returns:
        Canonicalized URL
    """
    if not url:
        return ""
    
    try:
        parsed = urlparse(url)
        
        # Remove common tracking parameters
        query_params = parse_qs(parsed.query)
        tracking_params = {
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
            'fbclid', 'gclid', 'ref', 'source', 'campaign', 'medium',
            'gclsrc', 'dclid', 'msclkid', 'mc_cid', 'mc_eid'
        }
        
        filtered_params = {k: v for k, v in query_params.items() 
                         if k not in tracking_params}
        
        # Rebuild query string
        new_query = '&'.join([f"{k}={v[0]}" for k, v in filtered_params.items()])
        
        # Remove fragment
        canonical_url = urlunparse((
            parsed.scheme, parsed.netloc, parsed.path,
            parsed.params, new_query, ''
        ))
        
        return canonical_url
        
    except Exception as e:
        logger.warning(f"Failed to canonicalize URL {url}: {e}")
        return url


def hash_content(title: str, domain: str) -> str:
    """
    Create hash for content deduplication.
    
    Args:
        title: Article title
        domain: Domain name
        
    Returns:
        MD5 hash string
    """
    content = f"{title}|{domain}".lower().strip()
    return hashlib.md5(content.encode('utf-8')).hexdigest()


def now_utc() -> datetime:
    """Get current UTC datetime."""
    return datetime.utcnow()


def parse_date_flexible(date_str: str) -> Optional[datetime]:
    """
    Parse date string with multiple format support.
    
    Args:
        date_str: Date string to parse
        
    Returns:
        Parsed datetime or None if parsing fails
    """
    if not date_str:
        return None
    
    # Common date formats
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
        '%d/%m/%Y %H:%M:%S',
        '%d/%m/%Y',
        '%m/%d/%Y %H:%M:%S',
        '%m/%d/%Y',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%dT%H:%M:%S.%fZ',
        '%a, %d %b %Y %H:%M:%S %Z',
        '%a, %d %b %Y %H:%M:%S %z',
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    # Try pandas parsing as fallback
    try:
        return pd.to_datetime(date_str).to_pydatetime()
    except:
        pass
    
    logger.warning(f"Could not parse date: {date_str}")
    return None


def window_count(df: pd.DataFrame, end_time: datetime, 
                hours: Optional[int] = None, days: Optional[int] = None,
                time_col: str = 'ts') -> pd.DataFrame:
    """
    Count events in time window.
    
    Args:
        df: DataFrame with timestamp column
        end_time: End time for window
        hours: Hours to look back
        days: Days to look back
        time_col: Name of timestamp column
        
    Returns:
        DataFrame with counts per node_id
    """
    if hours:
        start_time = end_time - timedelta(hours=hours)
    elif days:
        start_time = end_time - timedelta(days=days)
    else:
        raise ValueError("Must specify either hours or days")
    
    # Filter by time window
    mask = (df[time_col] >= start_time) & (df[time_col] <= end_time)
    window_df = df[mask].copy()
    
    # Count by node_id
    counts = window_df.groupby('node_id').size().reset_index(name='count')
    
    return counts


def neg_fraction(df: pd.DataFrame, hours: int = 72, 
                time_col: str = 'ts', sentiment_col: str = 'sentiment_score') -> pd.DataFrame:
    """
    Calculate negative sentiment fraction in time window.
    
    Args:
        df: DataFrame with sentiment scores
        hours: Hours to look back
        time_col: Name of timestamp column
        sentiment_col: Name of sentiment score column
        
    Returns:
        DataFrame with negative fraction per node_id
    """
    end_time = now_utc()
    start_time = end_time - timedelta(hours=hours)
    
    # Filter by time window
    mask = (df[time_col] >= start_time) & (df[time_col] <= end_time)
    window_df = df[mask].copy()
    
    # Calculate negative fraction
    def calc_neg_frac(group):
        if len(group) == 0:
            return 0.0
        neg_count = (group[sentiment_col] < 0).sum()
        return neg_count / len(group)
    
    neg_frac = window_df.groupby('node_id').apply(calc_neg_frac).reset_index()
    neg_frac.columns = ['node_id', 'neg_frac']
    
    return neg_frac


def strike_flag_7d(df: pd.DataFrame, days: int = 7, 
                  time_col: str = 'ts', event_type_col: str = 'event_type') -> pd.DataFrame:
    """
    Check for strike events in time window.
    
    Args:
        df: DataFrame with event types
        days: Days to look back
        time_col: Name of timestamp column
        event_type_col: Name of event type column
        
    Returns:
        DataFrame with strike flags per node_id
    """
    end_time = now_utc()
    start_time = end_time - timedelta(days=days)
    
    # Filter by time window and strike events
    mask = ((df[time_col] >= start_time) & (df[time_col] <= end_time) & 
            (df[event_type_col] == 'strike'))
    
    strike_df = df[mask].copy()
    
    # Create binary flag
    strike_flags = strike_df.groupby('node_id').size().reset_index(name='strike_count')
    strike_flags['strike_flag'] = (strike_flags['strike_count'] > 0).astype(int)
    
    return strike_flags[['node_id', 'strike_flag']]


def weather_flag(df: pd.DataFrame, days: int = 7, 
                time_col: str = 'ts') -> pd.DataFrame:
    """
    Check for weather anomalies in time window.
    
    Args:
        df: DataFrame with weather anomalies
        days: Days to look back
        time_col: Name of timestamp column
        
    Returns:
        DataFrame with weather flags per node_id
    """
    end_time = now_utc()
    start_time = end_time - timedelta(days=days)
    
    # Filter by time window
    mask = (df[time_col] >= start_time) & (df[time_col] <= end_time)
    weather_df = df[mask].copy()
    
    # Create binary flag
    weather_flags = weather_df.groupby('node_id').size().reset_index(name='weather_count')
    weather_flags['weather_flag'] = (weather_flags['weather_count'] > 0).astype(int)
    
    return weather_flags[['node_id', 'weather_flag']]


def news_velocity(df: pd.DataFrame, baseline_days: int = 30, 
                 time_col: str = 'ts', clip_value: float = 5.0) -> pd.DataFrame:
    """
    Calculate news velocity z-score vs baseline.
    
    Args:
        df: DataFrame with news events
        baseline_days: Days for baseline calculation
        time_col: Name of timestamp column
        clip_value: Maximum absolute z-score value
        
    Returns:
        DataFrame with velocity z-scores per node_id
    """
    end_time = now_utc()
    baseline_start = end_time - timedelta(days=baseline_days)
    recent_start = end_time - timedelta(days=1)  # Last 24 hours
    
    # Calculate baseline (daily counts over baseline period)
    baseline_df = df[df[time_col] >= baseline_start].copy()
    baseline_df['date'] = baseline_df[time_col].dt.date
    baseline_daily = baseline_df.groupby(['node_id', 'date']).size().reset_index(name='daily_count')
    
    # Calculate baseline stats per node
    baseline_stats = baseline_daily.groupby('node_id')['daily_count'].agg(['mean', 'std']).reset_index()
    baseline_stats['std'] = baseline_stats['std'].fillna(0)  # Handle nodes with no variance
    
    # Calculate recent count (last 24 hours)
    recent_df = df[(df[time_col] >= recent_start) & (df[time_col] <= end_time)]
    recent_counts = recent_df.groupby('node_id').size().reset_index(name='recent_count')
    
    # Ensure unique node_ids
    recent_counts = recent_counts.drop_duplicates(subset=['node_id'])
    baseline_stats = baseline_stats.drop_duplicates(subset=['node_id'])
    
    # Calculate z-scores
    velocity_df = recent_counts.merge(baseline_stats, on='node_id', how='left')
    velocity_df['mean'] = velocity_df['mean'].fillna(0)
    velocity_df['std'] = velocity_df['std'].fillna(1)  # Avoid division by zero
    
    # Calculate z-score
    velocity_df['z_score'] = (velocity_df['recent_count'] - velocity_df['mean']) / velocity_df['std']
    
    # Clip extreme values
    velocity_df['z_score'] = velocity_df['z_score'].clip(-clip_value, clip_value)
    
    return velocity_df[['node_id', 'z_score']].rename(columns={'z_score': 'news_velocity'})


def deduplicate_by_url(df: pd.DataFrame, url_col: str = 'url') -> pd.DataFrame:
    """
    Remove duplicate rows based on URL.
    
    Args:
        df: DataFrame to deduplicate
        url_col: Name of URL column
        
    Returns:
        Deduplicated DataFrame
    """
    # Canonicalize URLs
    df = df.copy()
    df['canonical_url'] = df[url_col].apply(canonicalize_url)
    
    # Keep first occurrence of each canonical URL
    deduplicated = df.drop_duplicates(subset=['canonical_url'], keep='first')
    
    # Remove temporary column
    deduplicated = deduplicated.drop(columns=['canonical_url'])
    
    logger.info(f"Deduplicated {len(df)} -> {len(deduplicated)} rows")
    return deduplicated


def clean_text(text: str) -> str:
    """
    Clean text for processing.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', '', text)
    
    return text


def extract_domain(url: str) -> str:
    """
    Extract domain from URL.
    
    Args:
        url: URL to extract domain from
        
    Returns:
        Domain name
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except:
        return ""


def is_valid_url(url: str) -> bool:
    """
    Check if URL is valid.
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid URL
    """
    try:
        parsed = urlparse(url)
        return bool(parsed.scheme and parsed.netloc)
    except:
        return False


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert value to float.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Float value
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """
    Safely convert value to int.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Integer value
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split list into chunks of specified size.
    
    Args:
        lst: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple dictionaries.
    
    Args:
        *dicts: Dictionaries to merge
        
    Returns:
        Merged dictionary
    """
    result = {}
    for d in dicts:
        result.update(d)
    return result
