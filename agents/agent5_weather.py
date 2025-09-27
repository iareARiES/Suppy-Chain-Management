"""
Agent 5: Weather Anomalies
Use Open-Meteo to detect weather anomalies for each node location.
"""
import logging
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import requests
import os

from core.models import WeatherAnomaly
from core.io import read_json, write_parquet
from core.utils import now_utc

logger = logging.getLogger(__name__)


class WeatherAgent:
    """Agent for fetching weather data and detecting anomalies."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.weather_api_key = os.getenv('WEATHER_API_KEY')
        # Use WeatherAPI.com service
        if self.weather_api_key:
            self.base_url = "http://api.weatherapi.com/v1"
            self.session = requests.Session()
        else:
            # Fallback to Open-Meteo if no API key
            self.base_url = "https://api.open-meteo.com/v1/forecast"
            self.session = requests.Session()
    
    def run(self, nodes: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Fetch weather data and detect anomalies for all nodes.
        
        Args:
            nodes: List of node dictionaries
            
        Returns:
            DataFrame with weather anomalies
        """
        logger.info("Starting weather agent...")
        
        weather_anomalies = []
        
        for node in nodes:
            anomalies = self._fetch_node_weather_anomalies(node)
            weather_anomalies.extend(anomalies)
        
        # Convert to DataFrame
        if weather_anomalies:
            df = pd.DataFrame(weather_anomalies)
        else:
            df = pd.DataFrame(columns=[
                'node_id', 'ts', 'anomaly_type', 'severity', 'value', 'threshold', 'duration_h'
            ])
        
        # Save to parquet
        self._save_weather_anomalies(df)
        
        logger.info(f"Weather agent completed. Detected {len(df)} weather anomalies")
        return df
    
    def _fetch_node_weather_anomalies(self, node: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch weather data and detect anomalies for a specific node.
        
        Args:
            node: Node dictionary
            
        Returns:
            List of weather anomaly dictionaries
        """
        anomalies = []
        lat = node.get('lat')
        lon = node.get('lon')
        node_id = node.get('node_id')
        
        if not lat or not lon:
            logger.warning(f"No coordinates for node {node_id}")
            return anomalies
        
        try:
            # Fetch weather data for last 7 days
            weather_data = self._fetch_weather_data(lat, lon)
            if not weather_data:
                return anomalies
            
            # Detect anomalies
            anomalies.extend(self._detect_precipitation_anomalies(node_id, weather_data))
            anomalies.extend(self._detect_temperature_anomalies(node_id, weather_data))
            anomalies.extend(self._detect_wind_anomalies(node_id, weather_data))
            
            logger.info(f"Detected {len(anomalies)} weather anomalies for {node_id}")
            
        except Exception as e:
            logger.warning(f"Failed to fetch weather data for {node_id}: {e}")
        
        return anomalies
    
    def _fetch_weather_data(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Fetch weather data from weather API.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Weather data dictionary or None if failed
        """
        try:
            if self.weather_api_key:
                # Use WeatherAPI.com
                params = {
                    'key': self.weather_api_key,
                    'q': f"{lat},{lon}",
                    'days': 7,
                    'aqi': 'no',
                    'alerts': 'no'
                }
                
                response = self.session.get(f"{self.base_url}/forecast.json", params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                # Convert WeatherAPI.com format to our expected format
                hourly_data = {
                    'temperature_2m': [],
                    'precipitation': [],
                    'wind_speed_10m': []
                }
                
                # Extract hourly data from forecast
                for day in data.get('forecast', {}).get('forecastday', []):
                    for hour in day.get('hour', []):
                        hourly_data['temperature_2m'].append(hour.get('temp_c', 0))
                        hourly_data['precipitation'].append(hour.get('precip_mm', 0))
                        hourly_data['wind_speed_10m'].append(hour.get('wind_kph', 0))
                
                return hourly_data
            else:
                # Fallback to Open-Meteo API (free, no key required)
                end_date = datetime.utcnow().date()
                start_date = end_date - timedelta(days=7)
                
                params = {
                    'latitude': lat,
                    'longitude': lon,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'hourly': 'temperature_2m,precipitation,wind_speed_10m',
                    'timezone': 'UTC'
                }
                
                response = self.session.get(self.base_url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                return data.get('hourly', {})
            
        except Exception as e:
            logger.warning(f"Failed to fetch weather data for {lat}, {lon}: {e}")
            return None
    
    def _detect_precipitation_anomalies(self, node_id: str, weather_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect heavy precipitation anomalies."""
        anomalies = []
        
        try:
            precipitation = weather_data.get('precipitation', [])
            if not precipitation:
                return anomalies
            
            # Threshold for heavy precipitation (40mm in 24h)
            heavy_precip_threshold = 40.0
            
            # Calculate 24-hour precipitation totals
            hourly_precip = precipitation
            daily_totals = []
            
            for i in range(0, len(hourly_precip), 24):
                day_precip = sum(hourly_precip[i:i+24])
                daily_totals.append(day_precip)
            
            # Check for heavy precipitation days
            for i, daily_total in enumerate(daily_totals):
                if daily_total > heavy_precip_threshold:
                    # Calculate severity
                    if daily_total > 100:
                        severity = 'high'
                    elif daily_total > 60:
                        severity = 'medium'
                    else:
                        severity = 'low'
                    
                    anomaly = {
                        'node_id': node_id,
                        'ts': datetime.utcnow() - timedelta(days=len(daily_totals)-i-1),
                        'anomaly_type': 'heavy_precip',
                        'severity': severity,
                        'value': daily_total,
                        'threshold': heavy_precip_threshold,
                        'duration_h': 24.0
                    }
                    anomalies.append(anomaly)
            
        except Exception as e:
            logger.warning(f"Failed to detect precipitation anomalies for {node_id}: {e}")
        
        return anomalies
    
    def _detect_temperature_anomalies(self, node_id: str, weather_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect extreme temperature anomalies."""
        anomalies = []
        
        try:
            temperatures = weather_data.get('temperature_2m', [])
            if not temperatures:
                return anomalies
            
            # Thresholds for extreme temperatures
            heatwave_threshold = 38.0  # Celsius
            cold_threshold = -10.0     # Celsius
            
            # Check for extreme temperatures
            for i, temp in enumerate(temperatures):
                if temp is not None:
                    if temp > heatwave_threshold:
                        # Calculate severity
                        if temp > 42:
                            severity = 'high'
                        elif temp > 40:
                            severity = 'medium'
                        else:
                            severity = 'low'
                        
                        anomaly = {
                            'node_id': node_id,
                            'ts': datetime.utcnow() - timedelta(hours=len(temperatures)-i-1),
                            'anomaly_type': 'extreme_heat',
                            'severity': severity,
                            'value': temp,
                            'threshold': heatwave_threshold,
                            'duration_h': 1.0
                        }
                        anomalies.append(anomaly)
                    
                    elif temp < cold_threshold:
                        # Calculate severity
                        if temp < -15:
                            severity = 'high'
                        elif temp < -12:
                            severity = 'medium'
                        else:
                            severity = 'low'
                        
                        anomaly = {
                            'node_id': node_id,
                            'ts': datetime.utcnow() - timedelta(hours=len(temperatures)-i-1),
                            'anomaly_type': 'extreme_cold',
                            'severity': severity,
                            'value': temp,
                            'threshold': cold_threshold,
                            'duration_h': 1.0
                        }
                        anomalies.append(anomaly)
            
        except Exception as e:
            logger.warning(f"Failed to detect temperature anomalies for {node_id}: {e}")
        
        return anomalies
    
    def _detect_wind_anomalies(self, node_id: str, weather_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect high wind anomalies."""
        anomalies = []
        
        try:
            wind_speeds = weather_data.get('wind_speed_10m', [])
            if not wind_speeds:
                return anomalies
            
            # Threshold for high wind (70 km/h)
            high_wind_threshold = 70.0
            
            # Check for high wind periods
            for i, wind_speed in enumerate(wind_speeds):
                if wind_speed is not None and wind_speed > high_wind_threshold:
                    # Calculate severity
                    if wind_speed > 100:
                        severity = 'high'
                    elif wind_speed > 85:
                        severity = 'medium'
                    else:
                        severity = 'low'
                    
                    anomaly = {
                        'node_id': node_id,
                        'ts': datetime.utcnow() - timedelta(hours=len(wind_speeds)-i-1),
                        'anomaly_type': 'high_wind',
                        'severity': severity,
                        'value': wind_speed,
                        'threshold': high_wind_threshold,
                        'duration_h': 1.0
                    }
                    anomalies.append(anomaly)
            
        except Exception as e:
            logger.warning(f"Failed to detect wind anomalies for {node_id}: {e}")
        
        return anomalies
    
    def _save_weather_anomalies(self, df: pd.DataFrame) -> None:
        """Save weather anomalies to parquet file."""
        output_path = self.data_dir / "outputs" / "weather_anomalies.parquet"
        write_parquet(df, str(output_path))
        logger.info(f"Saved {len(df)} weather anomalies to {output_path}")


def main():
    """Main function for running the weather agent."""
    # Load nodes
    nodes = read_json("data/outputs/nodes.json")
    
    agent = WeatherAgent()
    df = agent.run(nodes)
    print(f"Weather agent completed. Detected {len(df)} weather anomalies.")


if __name__ == "__main__":
    main()
