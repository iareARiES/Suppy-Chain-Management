"""
Enhanced geocoding service using Google Maps API via SerpApi.
"""
import os
import json
import requests
import logging
from typing import Optional, Tuple, Dict, Any, List
from functools import lru_cache

logger = logging.getLogger(__name__)


class GoogleMapsGeocoder:
    """Enhanced geocoding using Google Maps API via SerpApi."""
    
    def __init__(self, serp_api_key: str = None):
        self.serp_api_key = serp_api_key or os.getenv('SERP_API_KEY')
        self.base_url = "https://serpapi.com/search.json"
        self.session = requests.Session()
        self.cache = {}
        
        if not self.serp_api_key:
            logger.warning("SERP_API_KEY not found, Google Maps geocoding will be disabled")
    
    def _load_cache(self, cache_file: str = "cache/maps_geocoding.json"):
        """Load geocoding cache from file."""
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load maps cache: {e}")
                self.cache = {}
    
    def _save_cache(self, cache_file: str = "cache/maps_geocoding.json"):
        """Save geocoding cache to file."""
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Failed to save maps cache: {e}")
    
    def geocode_supplier(self, supplier_name: str, city: str = None, country: str = None) -> Optional[Dict[str, Any]]:
        """
        Geocode supplier using Google Maps API.
        
        Args:
            supplier_name: Name of the supplier/company
            city: City name (optional)
            country: Country name (optional)
            
        Returns:
            Dictionary with geocoding results or None if failed
        """
        if not self.serp_api_key:
            return None
        
        # Create cache key
        cache_key = f"supplier:{supplier_name.lower()}:{city or ''}:{country or ''}"
        
        # Check cache first
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Build search query
        query_parts = [supplier_name]
        if city:
            query_parts.append(city)
        if country:
            query_parts.append(country)
        
        query = " ".join(query_parts)
        
        try:
            params = {
                'engine': 'google_maps',
                'q': query,
                'api_key': self.serp_api_key,
                'type': 'search',
                'hl': 'en'
            }
            
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Extract results
            results = data.get('local_results', [])
            if not results:
                logger.warning(f"No Google Maps results found for: {query}")
                return None
            
            # Get the first result (most relevant)
            result = results[0]
            
            # Extract relevant information
            geocoding_result = {
                'name': result.get('title', supplier_name),
                'address': result.get('address', ''),
                'latitude': result.get('gps_coordinates', {}).get('latitude'),
                'longitude': result.get('gps_coordinates', {}).get('longitude'),
                'place_id': result.get('place_id', ''),
                'rating': result.get('rating'),
                'reviews': result.get('reviews'),
                'type': result.get('type', ''),
                'phone': result.get('phone', ''),
                'website': result.get('website', ''),
                'hours': result.get('hours', ''),
                'description': result.get('description', ''),
                'source': 'google_maps'
            }
            
            # Cache the result
            self.cache[cache_key] = geocoding_result
            self._save_cache()
            
            logger.info(f"Geocoded supplier '{supplier_name}' to {geocoding_result['latitude']}, {geocoding_result['longitude']}")
            return geocoding_result
            
        except Exception as e:
            logger.error(f"Google Maps geocoding failed for '{query}': {e}")
            return None
    
    def geocode_location(self, location_text: str) -> Optional[Dict[str, Any]]:
        """
        Geocode a location using Google Maps API.
        
        Args:
            location_text: Location description
            
        Returns:
            Dictionary with geocoding results or None if failed
        """
        if not self.serp_api_key:
            return None
        
        # Create cache key
        cache_key = f"location:{location_text.lower()}"
        
        # Check cache first
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            params = {
                'engine': 'google_maps',
                'q': location_text,
                'api_key': self.serp_api_key,
                'type': 'search',
                'hl': 'en'
            }
            
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Extract results
            results = data.get('local_results', [])
            if not results:
                logger.warning(f"No Google Maps results found for location: {location_text}")
                return None
            
            # Get the first result
            result = results[0]
            
            # Extract relevant information
            geocoding_result = {
                'name': result.get('title', location_text),
                'address': result.get('address', ''),
                'latitude': result.get('gps_coordinates', {}).get('latitude'),
                'longitude': result.get('gps_coordinates', {}).get('longitude'),
                'place_id': result.get('place_id', ''),
                'type': result.get('type', ''),
                'source': 'google_maps'
            }
            
            # Cache the result
            self.cache[cache_key] = geocoding_result
            self._save_cache()
            
            logger.info(f"Geocoded location '{location_text}' to {geocoding_result['latitude']}, {geocoding_result['longitude']}")
            return geocoding_result
            
        except Exception as e:
            logger.error(f"Google Maps geocoding failed for location '{location_text}': {e}")
            return None
    
    def search_nearby_suppliers(self, lat: float, lon: float, radius_km: float = 50.0, 
                               business_type: str = "manufacturing") -> List[Dict[str, Any]]:
        """
        Search for suppliers near a given location.
        
        Args:
            lat: Latitude
            lon: Longitude
            radius_km: Search radius in kilometers
            business_type: Type of business to search for
            
        Returns:
            List of supplier dictionaries
        """
        if not self.serp_api_key:
            return []
        
        try:
            # Convert radius to approximate meters (Google Maps uses meters)
            radius_m = int(radius_km * 1000)
            
            params = {
                'engine': 'google_maps',
                'q': f"{business_type} near {lat},{lon}",
                'api_key': self.serp_api_key,
                'type': 'search',
                'hl': 'en'
            }
            
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Extract results
            results = data.get('local_results', [])
            suppliers = []
            
            for result in results[:10]:  # Limit to top 10 results
                supplier = {
                    'name': result.get('title', ''),
                    'address': result.get('address', ''),
                    'latitude': result.get('gps_coordinates', {}).get('latitude'),
                    'longitude': result.get('gps_coordinates', {}).get('longitude'),
                    'place_id': result.get('place_id', ''),
                    'rating': result.get('rating'),
                    'reviews': result.get('reviews'),
                    'type': result.get('type', ''),
                    'phone': result.get('phone', ''),
                    'website': result.get('website', ''),
                    'distance_km': self._calculate_distance(lat, lon, 
                                                          result.get('gps_coordinates', {}).get('latitude', 0),
                                                          result.get('gps_coordinates', {}).get('longitude', 0))
                }
                suppliers.append(supplier)
            
            logger.info(f"Found {len(suppliers)} suppliers near {lat}, {lon}")
            return suppliers
            
        except Exception as e:
            logger.error(f"Nearby supplier search failed: {e}")
            return []
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in kilometers."""
        from math import radians, cos, sin, asin, sqrt
        
        # Haversine formula
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radius of earth in kilometers
        return c * r


# Global instance
_maps_geocoder = None

def get_maps_geocoder() -> GoogleMapsGeocoder:
    """Get global Google Maps geocoder instance."""
    global _maps_geocoder
    if _maps_geocoder is None:
        _maps_geocoder = GoogleMapsGeocoder()
    return _maps_geocoder
