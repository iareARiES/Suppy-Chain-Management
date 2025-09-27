"""
Geographic utilities for geocoding and distance calculations.
"""
import json
import os
from typing import Optional, Tuple, Dict, Any
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import logging
from functools import lru_cache

from .google_maps_geocoder import get_google_maps_geocoder

logger = logging.getLogger(__name__)


class GeoCache:
    """Simple file-based cache for geocoding results."""
    
    def __init__(self, cache_file: str = "cache/geocoding.json"):
        self.cache_file = cache_file
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict[str, Dict[str, Any]]:
        """Load cache from file."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load geo cache: {e}")
        return {}
    
    def _save_cache(self):
        """Save cache to file."""
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Failed to save geo cache: {e}")
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached geocoding result."""
        return self.cache.get(key)
    
    def set(self, key: str, value: Dict[str, Any]):
        """Set cached geocoding result."""
        self.cache[key] = value
        self._save_cache()


class Geocoder:
    """Geocoding service with caching and multiple providers."""
    
    def __init__(self, cache_file: str = "cache/geocoding.json"):
        self.cache = GeoCache(cache_file)
        self.geocoder = Nominatim(user_agent="supply-chain-risk-analysis")
        
        # Initialize Google Maps geocoder
        self.google_maps_geocoder = get_google_maps_geocoder()
        
        # Try OpenCage if API key is available
        self.opencage_geocoder = None
        opencage_key = os.getenv('OPENCAGE_KEY')
        if opencage_key:
            try:
                from geopy.geocoders import OpenCage
                self.opencage_geocoder = OpenCage(api_key=opencage_key)
                logger.info("OpenCage geocoder initialized")
            except ImportError:
                logger.warning("OpenCage not available, using Nominatim only")
    
    @lru_cache(maxsize=1000)
    def geocode_city_country(self, city: str, country: str) -> Optional[Tuple[float, float]]:
        """
        Geocode city and country to lat/lon coordinates.
        
        Args:
            city: City name
            country: Country name
            
        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        # Create cache key
        cache_key = f"{city.lower()},{country.lower()}"
        
        # Check cache first
        cached = self.cache.get(cache_key)
        if cached:
            return (cached['lat'], cached['lon'])
        
        # Try geocoding with multiple providers
        query = f"{city}, {country}"
        result = None
        
        # Try Google Maps first if available
        if self.google_maps_geocoder and self.google_maps_geocoder.api_key:
            try:
                google_result = self.google_maps_geocoder.geocode_address(query)
                if google_result:
                    lat, lon = google_result['lat'], google_result['lng']
                    # Cache the result
                    self.cache.set(cache_key, {'lat': lat, 'lon': lon})
                    return (lat, lon)
            except Exception as e:
                logger.warning(f"Google Maps geocoding failed for {query}: {e}")
        
        # Try OpenCage if available
        if self.opencage_geocoder:
            try:
                result = self.opencage_geocoder.geocode(query, timeout=10)
            except Exception as e:
                logger.warning(f"OpenCage geocoding failed for {query}: {e}")
        
        # Fallback to Nominatim
        if not result:
            try:
                result = self.geocoder.geocode(query, timeout=10)
            except Exception as e:
                logger.warning(f"Geocoding failed for {query}: {e}")
                return None
        
        if result:
            lat, lon = result.latitude, result.longitude
            # Cache the result
            self.cache.set(cache_key, {'lat': lat, 'lon': lon})
            return (lat, lon)
        
        return None
    
    def geocode_text(self, text: str) -> Optional[Tuple[float, float]]:
        """
        Geocode arbitrary text to lat/lon coordinates.
        
        Args:
            text: Text containing location information
            
        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        # Check cache first
        cache_key = f"text:{text.lower()}"
        cached = self.cache.get(cache_key)
        if cached:
            return (cached['lat'], cached['lon'])
        
        # Try geocoding with multiple providers
        result = None
        
        # Try Google Maps first if available
        if self.google_maps_geocoder and self.google_maps_geocoder.api_key:
            try:
                google_result = self.google_maps_geocoder.geocode_address(text)
                if google_result:
                    lat, lon = google_result['lat'], google_result['lng']
                    # Cache the result
                    self.cache.set(cache_key, {'lat': lat, 'lon': lon})
                    return (lat, lon)
            except Exception as e:
                logger.warning(f"Google Maps geocoding failed for {text}: {e}")
        
        # Try OpenCage if available
        if self.opencage_geocoder:
            try:
                result = self.opencage_geocoder.geocode(text, timeout=10)
            except Exception as e:
                logger.warning(f"OpenCage geocoding failed for {text}: {e}")
        
        # Fallback to Nominatim
        if not result:
            try:
                result = self.geocoder.geocode(text, timeout=10)
            except Exception as e:
                logger.warning(f"Geocoding failed for {text}: {e}")
                return None
        
        if result:
            lat, lon = result.latitude, result.longitude
            # Cache the result
            self.cache.set(cache_key, {'lat': lat, 'lon': lon})
            return (lat, lon)
        
        return None
    
    def geocode_company(self, company_name: str, city: str = "", country: str = "") -> Optional[Tuple[float, float]]:
        """
        Geocode a company by name and location using Google Maps.
        
        Args:
            company_name: Company name
            city: City name (optional)
            country: Country name (optional)
            
        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        if self.google_maps_geocoder and self.google_maps_geocoder.api_key:
            return self.google_maps_geocoder.geocode_company(company_name, city, country)
        
        # Fallback to text geocoding
        query_parts = [company_name]
        if city:
            query_parts.append(city)
        if country:
            query_parts.append(country)
        
        return self.geocode_text(", ".join(query_parts))


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth.
    
    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates
        
    Returns:
        Distance in kilometers
    """
    return geodesic((lat1, lon1), (lat2, lon2)).kilometers


def find_nearest_node(target_lat: float, target_lon: float, nodes: list, max_distance_km: float = 80.0) -> Optional[str]:
    """
    Find the nearest node to given coordinates.
    
    Args:
        target_lat: Target latitude
        target_lon: Target longitude
        nodes: List of node dictionaries with 'lat', 'lon', 'node_id'
        max_distance_km: Maximum distance to consider
        
    Returns:
        Node ID of nearest node or None if none within max_distance_km
    """
    nearest_node = None
    min_distance = float('inf')
    
    for node in nodes:
        distance = haversine_distance(
            target_lat, target_lon,
            node['lat'], node['lon']
        )
        
        if distance < min_distance and distance <= max_distance_km:
            min_distance = distance
            nearest_node = node['node_id']
    
    return nearest_node


def extract_location_from_text(text: str) -> list:
    """
    Extract potential location names from text.
    
    Args:
        text: Text to analyze
        
    Returns:
        List of potential location strings
    """
    import re
    
    # Common location patterns
    patterns = [
        r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Industrial\s+)?Park\b',
        r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:District|Zone|Area)\b',
        r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:City|Town|Village)\b',
        r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Province|State|Prefecture)\b',
        r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Factory|Plant|Facility)\b',
    ]
    
    locations = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        locations.extend(matches)
    
    # Also look for standalone city names (simple heuristic)
    city_pattern = r'\b[A-Z][a-z]{2,}(?:\s+[A-Z][a-z]+)*\b'
    city_matches = re.findall(city_pattern, text)
    
    # Filter out common non-location words
    exclude_words = {
        'Company', 'Corporation', 'Limited', 'Inc', 'Ltd', 'Group', 'Technology',
        'Electronics', 'Precision', 'Industries', 'Systems', 'Solutions', 'Services',
        'Manufacturing', 'Production', 'Assembly', 'Testing', 'Quality', 'Control',
        'Management', 'Operations', 'Business', 'Development', 'Research', 'Design'
    }
    
    for match in city_matches:
        if not any(word in match for word in exclude_words):
            locations.append(match)
    
    return list(set(locations))  # Remove duplicates


# Global geocoder instance
_geocoder = None

def get_geocoder() -> Geocoder:
    """Get global geocoder instance."""
    global _geocoder
    if _geocoder is None:
        _geocoder = Geocoder()
    return _geocoder
