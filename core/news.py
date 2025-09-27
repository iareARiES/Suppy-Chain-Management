"""
News fetching utilities for RSS feeds and SERP API.
"""
import os
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import feedparser
import requests
from urllib.parse import urljoin, urlparse
import time

logger = logging.getLogger(__name__)


class RSSFetcher:
    """RSS feed fetcher with caching and error handling."""
    
    def __init__(self, cache_duration_hours: int = 1):
        self.cache_duration = timedelta(hours=cache_duration_hours)
        self.cache = {}
    
    def fetch_rss_feed(self, url: str) -> List[Dict[str, Any]]:
        """
        Fetch and parse RSS feed.
        
        Args:
            url: RSS feed URL
            
        Returns:
            List of article dictionaries
        """
        # Check cache first
        cache_key = f"rss:{url}"
        if cache_key in self.cache:
            cached_time, articles = self.cache[cache_key]
            if datetime.utcnow() - cached_time < self.cache_duration:
                return articles
        
        try:
            feed = feedparser.parse(url)
            articles = []
            
            for entry in feed.entries:
                article = {
                    'url': entry.get('link', ''),
                    'headline': entry.get('title', ''),
                    'snippet': entry.get('summary', ''),
                    'outlet': self._extract_outlet_from_url(entry.get('link', '')),
                    'ts': self._parse_date(entry.get('published', '')),
                    'source': 'rss'
                }
                
                # Only include recent articles (last 7 days)
                if article['ts'] and article['ts'] > datetime.utcnow() - timedelta(days=7):
                    articles.append(article)
            
            # Cache the results
            self.cache[cache_key] = (datetime.utcnow(), articles)
            logger.info(f"Fetched {len(articles)} articles from RSS feed: {url}")
            return articles
            
        except Exception as e:
            logger.error(f"Failed to fetch RSS feed {url}: {e}")
            return []
    
    def _extract_outlet_from_url(self, url: str) -> str:
        """Extract outlet name from URL."""
        try:
            domain = urlparse(url).netloc
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return 'unknown'
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime."""
        if not date_str:
            return None
        
        try:
            # Try parsing with feedparser's parsed date
            import time
            if hasattr(time, 'struct_time'):
                parsed_time = time.strptime(date_str, '%a, %d %b %Y %H:%M:%S %Z')
                return datetime(*parsed_time[:6])
        except:
            pass
        
        # Fallback to current time if parsing fails
        return datetime.utcnow()


class SERPClient:
    """SERP API client for Google search results."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://serpapi.com/search.json"
        self.session = requests.Session()
    
    def search(self, query: str, num_results: int = 10, country: str = "us", 
               language: str = "en") -> List[Dict[str, Any]]:
        """
        Search using SERP API.
        
        Args:
            query: Search query
            num_results: Number of results to return
            country: Country code
            language: Language code
            
        Returns:
            List of search result dictionaries
        """
        params = {
            'q': query,
            'api_key': self.api_key,
            'engine': 'google',
            'num': num_results,
            'gl': country,
            'hl': language,
            'safe': 'off'
        }
        
        try:
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            articles = []
            for result in data.get('organic_results', []):
                article = {
                    'url': result.get('link', ''),
                    'headline': result.get('title', ''),
                    'snippet': result.get('snippet', ''),
                    'outlet': self._extract_outlet_from_url(result.get('link', '')),
                    'ts': datetime.utcnow(),  # SERP doesn't provide timestamps
                    'source': 'serp'
                }
                articles.append(article)
            
            logger.info(f"SERP search returned {len(articles)} results for query: {query}")
            return articles
            
        except Exception as e:
            logger.error(f"SERP API request failed: {e}")
            return []
    
    def _extract_outlet_from_url(self, url: str) -> str:
        """Extract outlet name from URL."""
        try:
            domain = urlparse(url).netloc
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return 'unknown'


class NewsAggregator:
    """Aggregates news from multiple sources."""
    
    def __init__(self, serp_api_key: str):
        self.rss_fetcher = RSSFetcher()
        self.serp_client = SERPClient(serp_api_key)
        self.seen_urls = set()  # For deduplication
    
    def fetch_rss_allowlist(self, allowlist: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch news from all RSS feeds in allowlist.
        
        Args:
            allowlist: Region allowlist configuration
            
        Returns:
            List of article dictionaries
        """
        all_articles = []
        
        for region_key, region_data in allowlist.get('regions', {}).items():
            outlets = region_data.get('outlets', [])
            
            for outlet in outlets:
                rss_url = outlet.get('rss')
                if rss_url:
                    articles = self.rss_fetcher.fetch_rss_feed(rss_url)
                    # Add region info
                    for article in articles:
                        article['region'] = region_key
                    all_articles.extend(articles)
        
        return all_articles
    
    def serp_discover(self, node: Dict[str, Any], allowlist: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Discover news using SERP API for a specific node.
        
        Args:
            node: Node information
            allowlist: Region allowlist configuration
            
        Returns:
            List of article dictionaries
        """
        articles = []
        supplier_name = node.get('name', '')
        city = node.get('city', '')
        country = node.get('country', '')
        
        # Build search queries
        queries = []
        
        # Basic supplier + location query
        if supplier_name and city:
            queries.append(f'"{supplier_name}" {city} factory OR plant OR PCB OR EMS OR shutdown OR strike OR flood')
        
        # Supplier + country query
        if supplier_name and country:
            queries.append(f'"{supplier_name}" {country} production OR facility OR news')
        
        # Location-based queries
        if city and country:
            queries.append(f'{city} {country} industrial OR manufacturing OR electronics OR strike OR flood')
        
        # Get preferred outlets for the region
        region_outlets = []
        for region_key, region_data in allowlist.get('regions', {}).items():
            if (node.get('region') == region_key or 
                node.get('country', '').lower() in region_key.lower()):
                outlets = region_data.get('outlets', [])
                region_outlets.extend([outlet.get('domain', '') for outlet in outlets])
        
        # Add site-specific queries
        for query in queries[:2]:  # Limit to avoid too many requests
            if region_outlets:
                site_query = f"{query} site:{' OR site:'.join(region_outlets[:3])}"
                articles.extend(self.serp_client.search(site_query, num_results=5))
            
            # Also search without site restriction
            articles.extend(self.serp_client.search(query, num_results=5))
        
        # Add region info and deduplicate
        for article in articles:
            article['region'] = node.get('region', 'unknown')
        
        return self._deduplicate_articles(articles)
    
    def _deduplicate_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate articles based on URL."""
        unique_articles = []
        
        for article in articles:
            url = article.get('url', '')
            if url and url not in self.seen_urls:
                self.seen_urls.add(url)
                unique_articles.append(article)
        
        return unique_articles
    
    def canonicalize_url(self, url: str) -> str:
        """Canonicalize URL by removing tracking parameters."""
        try:
            from urllib.parse import urlparse, urlunparse, parse_qs
            parsed = urlparse(url)
            
            # Remove common tracking parameters
            query_params = parse_qs(parsed.query)
            tracking_params = {'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 
                             'utm_content', 'fbclid', 'gclid', 'ref'}
            
            filtered_params = {k: v for k, v in query_params.items() 
                             if k not in tracking_params}
            
            # Rebuild query string
            new_query = '&'.join([f"{k}={v[0]}" for k, v in filtered_params.items()])
            
            return urlunparse((
                parsed.scheme, parsed.netloc, parsed.path,
                parsed.params, new_query, ''  # Remove fragment
            ))
        except:
            return url


def build_serp_queries(node: Dict[str, Any], allowlist: Dict[str, Any]) -> List[str]:
    """
    Build SERP search queries for a node.
    
    Args:
        node: Node information
        allowlist: Region allowlist configuration
        
    Returns:
        List of search queries
    """
    queries = []
    supplier_name = node.get('name', '')
    city = node.get('city', '')
    country = node.get('country', '')
    
    # Get preferred outlets for the region
    preferred_domains = []
    for region_key, region_data in allowlist.get('regions', {}).items():
        if (node.get('region') == region_key or 
            node.get('country', '').lower() in region_key.lower()):
            outlets = region_data.get('outlets', [])
            preferred_domains.extend([outlet.get('domain', '') for outlet in outlets])
    
    # Build queries
    if supplier_name and city:
        base_query = f'"{supplier_name}" {city} factory OR plant OR PCB OR EMS OR shutdown OR strike OR flood'
        
        if preferred_domains:
            site_query = f"{base_query} site:{' OR site:'.join(preferred_domains[:3])}"
            queries.append(site_query)
        
        queries.append(base_query)
    
    return queries
