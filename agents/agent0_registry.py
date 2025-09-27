"""
Agent 0: Registry/Normalizer
Build canonical nodes.json from seed suppliers with geocoding.
"""
import logging
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path

from core.models import Node, AllowlistConfig
from core.geo import get_geocoder
from core.io import read_csv, write_json, read_yaml

logger = logging.getLogger(__name__)


class RegistryAgent:
    """Agent for building and maintaining the supplier registry."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.geocoder = get_geocoder()
    
    def run(self) -> List[Dict[str, Any]]:
        """
        Build canonical nodes from seed suppliers.
        
        Returns:
            List of node dictionaries
        """
        logger.info("Starting registry agent...")
        
        # Load seed suppliers
        suppliers_df = self._load_suppliers()
        logger.info(f"Loaded {len(suppliers_df)} suppliers from seed data")
        
        # Load allowlist for region mapping
        allowlist = self._load_allowlist()
        
        # Process each supplier
        nodes = []
        for _, supplier in suppliers_df.iterrows():
            node = self._process_supplier(supplier, allowlist)
            if node:
                nodes.append(node)
        
        # Save nodes to JSON
        self._save_nodes(nodes)
        
        logger.info(f"Registry agent completed. Created {len(nodes)} nodes")
        return nodes
    
    def _load_suppliers(self) -> pd.DataFrame:
        """Load suppliers from seed CSV."""
        suppliers_path = self.data_dir / "inputs" / "suppliers_seed.csv"
        return read_csv(str(suppliers_path))
    
    def _load_allowlist(self) -> Dict[str, Any]:
        """Load region allowlist configuration."""
        allowlist_path = self.data_dir / "inputs" / "allowlist_regions.yaml"
        return read_yaml(str(allowlist_path))
    
    def _process_supplier(self, supplier: pd.Series, allowlist: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a single supplier into a node.
        
        Args:
            supplier: Supplier data row
            allowlist: Region allowlist configuration
            
        Returns:
            Node dictionary or None if processing fails
        """
        try:
            name = supplier['name']
            country = supplier.get('country', '') or ''
            city = supplier.get('city', '') or ''
            
            # Handle NaN values from pandas
            if pd.isna(country):
                country = ''
            if pd.isna(city):
                city = ''
            
            # Geocode location
            lat, lon = self._geocode_location(city, country, name)
            if lat is None or lon is None:
                logger.warning(f"Could not geocode {name} in {city}, {country}")
                return None
            
            # Determine region from country
            region = self._determine_region(country, allowlist)
            
            # Generate node_id
            node_id = self._generate_node_id(name, country, city, lat, lon)
            
            # Create node
            node = {
                'node_id': node_id,
                'node_type': 'supplier',
                'name': name,
                'country': country,
                'city': city,
                'lat': lat,
                'lon': lon,
                'tier': 1.0,
                'category': supplier.get('category', ''),
                'site_url': supplier.get('site_url', ''),
                'alt_url': supplier.get('alt_url', ''),
                'x_handle': supplier.get('x_handle', ''),
                'ticker': supplier.get('ticker', ''),
                'region': region
            }
            
            logger.info(f"Created node: {node_id} for {name}")
            return node
            
        except Exception as e:
            logger.error(f"Failed to process supplier {supplier.get('name', 'unknown')}: {e}")
            return None
    
    def _geocode_location(self, city: str, country: str, name: str) -> tuple:
        """
        Geocode location to lat/lon coordinates using Google Maps API.
        
        Args:
            city: City name
            country: Country name
            name: Supplier name (for fallback)
            
        Returns:
            Tuple of (lat, lon) or (None, None) if geocoding fails
        """
        # Try company geocoding first (Google Maps)
        if name:
            coords = self.geocoder.geocode_company(name, city, country)
            if coords:
                logger.info(f"Google Maps geocoded '{name}' to {coords[0]}, {coords[1]}")
                return coords
        
        # Fallback to city, country geocoding
        if city and country:
            coords = self.geocoder.geocode_city_country(city, country)
            if coords:
                return coords
        
        # Try country only
        if country:
            coords = self.geocoder.geocode_city_country(country, country)
            if coords:
                return coords
        
        # Try supplier name as fallback
        if name:
            coords = self.geocoder.geocode_text(name)
            if coords:
                return coords
        
        return None, None
    
    def _determine_region(self, country: str, allowlist: Dict[str, Any]) -> str:
        """
        Determine region from country name.
        
        Args:
            country: Country name
            allowlist: Region allowlist configuration
            
        Returns:
            Region key
        """
        if not country or pd.isna(country) or country == '':
            return 'global'
        
        country_lower = str(country).lower()
        
        # Map countries to regions
        country_region_map = {
            'china': 'china',
            'taiwan': 'taiwan',
            'south korea': 'south_korea',
            'vietnam': 'vietnam',
            'thailand': 'thailand',
            'malaysia': 'malaysia',
            'india': 'india',
            'japan': 'japan'
        }
        
        for country_key, region in country_region_map.items():
            if country_key in country_lower:
                return region
        
        return 'global'
    
    def _generate_node_id(self, name: str, country: str, city: str, lat: float, lon: float) -> str:
        """
        Generate canonical node ID.
        
        Args:
            name: Supplier name
            country: Country name
            city: City name
            lat: Latitude
            lon: Longitude
            
        Returns:
            Node ID string
        """
        # Clean and format components
        clean_name = name.replace(' ', '-').replace(',', '').replace('.', '').replace('(', '').replace(')', '').replace('/', '-')
        clean_country = country.replace(' ', '-')
        clean_city = city.replace(' ', '-') if city else 'Unknown'
        
        # Create node ID
        node_id = f"{clean_country}_{clean_city}_{clean_name}_{lat:.2f}_{lon:.2f}"
        
        return node_id
    
    def _save_nodes(self, nodes: List[Dict[str, Any]]) -> None:
        """Save nodes to JSON file."""
        output_path = self.data_dir / "outputs" / "nodes.json"
        write_json(nodes, str(output_path))
        logger.info(f"Saved {len(nodes)} nodes to {output_path}")


def main():
    """Main function for running the registry agent."""
    agent = RegistryAgent()
    nodes = agent.run()
    print(f"Registry agent completed. Created {len(nodes)} nodes.")


if __name__ == "__main__":
    main()
