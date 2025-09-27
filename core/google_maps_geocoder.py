"""
Google Maps Geocoding API integration for location services.
"""
import os
import json
import requests
import logging
from typing import Optional, Tuple, Dict, Any, List
from functools import lru_cache
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class GoogleMapsGeocoder:
    """Google Maps Geocoding API client with caching."""
    
    def __init__(self, api_key: Optional[str] = None, cache_file: str = "cache/google_maps_geocoding.json"):
        self.api_key = api_key or os.getenv('GOOGLE_MAPS_API_KEY')
        self.cache_file = cache_file
        self.cache = self._load_cache()
        self.base_url = "https://maps.googleapis.com/maps/api/geocode/json"
        
        if not self.api_key:
            logger.warning("Google Maps API key not provided")
        else:
            logger.info("Google Maps Geocoder initialized")
    
    def _load_cache(self) -> Dict[str, Dict[str, Any]]:
        """Load cache from file."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load Google Maps cache: {e}")
        return {}
    
    def _save_cache(self):
        """Save cache to file."""
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Failed to save Google Maps cache: {e}")
    
    def _get_cache_key(self, address: str) -> str:
        """Generate cache key for address."""
        return address.lower().strip()
    
    def geocode_address(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Geocode an address using Google Maps API.
        
        Args:
            address: Address to geocode
            
        Returns:
            Dictionary with geocoding results or None if failed
        """
        if not self.api_key:
            logger.warning("Google Maps API key not available")
            return None
        
        # Check cache first
        cache_key = self._get_cache_key(address)
        if cache_key in self.cache:
            logger.debug(f"Using cached result for: {address}")
            return self.cache[cache_key]
        
        # Prepare request
        params = {
            'address': address,
            'key': self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                result = data['results'][0]  # Take first result
                
                # Extract coordinates
                location = result['geometry']['location']
                lat = location['lat']
                lng = location['lng']
                
                # Extract formatted address
                formatted_address = result['formatted_address']
                
                # Extract address components
                components = {}
                for component in result.get('address_components', []):
                    types = component['types']
                    if 'country' in types:
                        components['country'] = component['long_name']
                        components['country_code'] = component['short_name']
                    elif 'administrative_area_level_1' in types:
                        components['state'] = component['long_name']
                    elif 'locality' in types:
                        components['city'] = component['long_name']
                    elif 'postal_code' in types:
                        components['postal_code'] = component['long_name']
                
                geocoding_result = {
                    'lat': lat,
                    'lng': lng,
                    'formatted_address': formatted_address,
                    'components': components,
                    'place_id': result.get('place_id'),
                    'types': result.get('types', [])
                }
                
                # Cache the result
                self.cache[cache_key] = geocoding_result
                self._save_cache()
                
                logger.info(f"Geocoded: {address} -> {lat}, {lng}")
                return geocoding_result
            
            elif data['status'] == 'ZERO_RESULTS':
                logger.warning(f"No results found for address: {address}")
                # Cache negative result
                self.cache[cache_key] = None
                self._save_cache()
                return None
            
            else:
                logger.error(f"Google Maps API error for {address}: {data['status']} - {data.get('error_message', '')}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Google Maps API request failed for {address}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error geocoding {address}: {e}")
            return None
    
    def geocode_company(self, company_name: str, city: str = "", country: str = "") -> Optional[Tuple[float, float]]:
        """
        Geocode a company by name and location.
        
        Args:
            company_name: Company name
            city: City name (optional)
            country: Country name (optional)
            
        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        # Build search query
        query_parts = [company_name]
        if city:
            query_parts.append(city)
        if country:
            query_parts.append(country)
        
        address = ", ".join(query_parts)
        
        result = self.geocode_address(address)
        if result:
            return (result['lat'], result['lng'])
        
        return None
    
    def reverse_geocode(self, lat: float, lng: float) -> Optional[Dict[str, Any]]:
        """
        Reverse geocode coordinates to address.
        
        Args:
            lat: Latitude
            lng: Longitude
            
        Returns:
            Dictionary with address information or None if failed
        """
        if not self.api_key:
            logger.warning("Google Maps API key not available")
            return None
        
        # Check cache first
        cache_key = f"reverse:{lat},{lng}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Prepare request
        params = {
            'latlng': f"{lat},{lng}",
            'key': self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                result = data['results'][0]
                
                # Extract address components
                components = {}
                for component in result.get('address_components', []):
                    types = component['types']
                    if 'country' in types:
                        components['country'] = component['long_name']
                        components['country_code'] = component['short_name']
                    elif 'administrative_area_level_1' in types:
                        components['state'] = component['long_name']
                    elif 'locality' in types:
                        components['city'] = component['long_name']
                    elif 'postal_code' in types:
                        components['postal_code'] = component['long_name']
                
                reverse_result = {
                    'formatted_address': result['formatted_address'],
                    'components': components,
                    'place_id': result.get('place_id'),
                    'types': result.get('types', [])
                }
                
                # Cache the result
                self.cache[cache_key] = reverse_result
                self._save_cache()
                
                return reverse_result
            
            else:
                logger.warning(f"Reverse geocoding failed: {data['status']}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Reverse geocoding request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in reverse geocoding: {e}")
            return None
    
    def get_place_details(self, place_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a place using its place_id.
        
        Args:
            place_id: Google Places place_id
            
        Returns:
            Dictionary with place details or None if failed
        """
        if not self.api_key:
            logger.warning("Google Maps API key not available")
            return None
        
        # Check cache first
        cache_key = f"place:{place_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Prepare request
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            'place_id': place_id,
            'key': self.api_key,
            'fields': 'name,formatted_address,geometry,types,website,formatted_phone_number'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK' and 'result' in data:
                result = data['result']
                
                place_details = {
                    'name': result.get('name'),
                    'formatted_address': result.get('formatted_address'),
                    'geometry': result.get('geometry'),
                    'types': result.get('types', []),
                    'website': result.get('website'),
                    'formatted_phone_number': result.get('formatted_phone_number')
                }
                
                # Cache the result
                self.cache[cache_key] = place_details
                self._save_cache()
                
                return place_details
            
            else:
                logger.warning(f"Place details failed: {data['status']}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Place details request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting place details: {e}")
            return None
    
    def search_places(self, query: str, location: Optional[Tuple[float, float]] = None, radius: int = 50000) -> List[Dict[str, Any]]:
        """
        Search for places using Google Places API.
        
        Args:
            query: Search query
            location: Optional (lat, lng) to bias search results
            radius: Search radius in meters (default: 50km)
            
        Returns:
            List of place dictionaries
        """
        if not self.api_key:
            logger.warning("Google Maps API key not available")
            return []
        
        # Check cache first
        cache_key = f"search:{query}:{location}:{radius}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Prepare request
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            'query': query,
            'key': self.api_key
        }
        
        if location:
            params['location'] = f"{location[0]},{location[1]}"
            params['radius'] = radius
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK':
                places = []
                for result in data.get('results', []):
                    place = {
                        'name': result.get('name'),
                        'formatted_address': result.get('formatted_address'),
                        'geometry': result.get('geometry'),
                        'place_id': result.get('place_id'),
                        'types': result.get('types', []),
                        'rating': result.get('rating'),
                        'user_ratings_total': result.get('user_ratings_total')
                    }
                    places.append(place)
                
                # Cache the results
                self.cache[cache_key] = places
                self._save_cache()
                
                return places
            
            else:
                logger.warning(f"Place search failed: {data['status']}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Place search request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in place search: {e}")
            return []


# Global Google Maps geocoder instance
_google_maps_geocoder = None

def get_google_maps_geocoder() -> GoogleMapsGeocoder:
    """Get global Google Maps geocoder instance."""
    global _google_maps_geocoder
    if _google_maps_geocoder is None:
        _google_maps_geocoder = GoogleMapsGeocoder()
    return _google_maps_geocoder
