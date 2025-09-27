"""
Agent 6: Feature Builder
Join all data sources and compute ML features.
"""
import logging
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

from core.models import FeatureRow
from core.io import read_json, read_parquet, safe_read_parquet
from core.utils import (
    window_count, neg_fraction, strike_flag_7d, weather_flag, 
    news_velocity, now_utc
)

logger = logging.getLogger(__name__)


class FeatureAgent:
    """Agent for building ML features from all data sources."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
    
    def run(self, nodes: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Build features from all data sources.
        
        Args:
            nodes: List of node dictionaries
            
        Returns:
            DataFrame with computed features
        """
        logger.info("Starting feature agent...")
        
        # Load all data sources
        news_df = self._load_news_data()
        social_df = self._load_social_data()
        events_df = self._load_events_data()
        weather_df = self._load_weather_data()
        
        # Build features for each node
        features = []
        for node in nodes:
            node_features = self._build_node_features(
                node, news_df, social_df, events_df, weather_df
            )
            features.append(node_features)
        
        # Convert to DataFrame
        df = pd.DataFrame(features)
        
        # Ensure all required columns are present with proper types
        df = self._ensure_schema(df)
        
        logger.info(f"Feature agent completed. Built features for {len(df)} nodes")
        return df
    
    def _load_news_data(self) -> pd.DataFrame:
        """Load news events data."""
        news_path = self.data_dir / "outputs" / "news_events.parquet"
        return safe_read_parquet(str(news_path), default=pd.DataFrame())
    
    def _load_social_data(self) -> pd.DataFrame:
        """Load social events data."""
        social_path = self.data_dir / "outputs" / "social_events.parquet"
        return safe_read_parquet(str(social_path), default=pd.DataFrame())
    
    def _load_events_data(self) -> pd.DataFrame:
        """Load extracted events data."""
        events_path = self.data_dir / "outputs" / "extracted_events.parquet"
        return safe_read_parquet(str(events_path), default=pd.DataFrame())
    
    def _load_weather_data(self) -> pd.DataFrame:
        """Load weather anomalies data."""
        weather_path = self.data_dir / "outputs" / "weather_anomalies.parquet"
        return safe_read_parquet(str(weather_path), default=pd.DataFrame())
    
    
    def _build_node_features(self, node: Dict[str, Any], news_df: pd.DataFrame,
                           social_df: pd.DataFrame, events_df: pd.DataFrame,
                           weather_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Build features for a single node.
        
        Args:
            node: Node dictionary
            news_df: News events DataFrame
            social_df: Social events DataFrame
            events_df: Extracted events DataFrame
            weather_df: Weather anomalies DataFrame
            market_df: Market signals DataFrame
            
        Returns:
            Dictionary with computed features
        """
        node_id = node['node_id']
        now = now_utc()
        
        # Initialize feature dictionary with node info
        features = {
            'node_id': node_id,
            'node_type': node.get('node_type', 'supplier'),
            'name': node.get('name', ''),
            'country': node.get('country', ''),
            'lat': float(node.get('lat', 0.0)),
            'lon': float(node.get('lon', 0.0)),
            'tier': float(node.get('tier', 1.0))
        }
        
        # News features
        features.update(self._compute_news_features(node_id, news_df, now))
        
        # Social features (combine with news for sentiment)
        features.update(self._compute_social_features(node_id, social_df, now))
        
        # Event features
        features.update(self._compute_event_features(node_id, events_df, now))
        
        # Weather features
        features.update(self._compute_weather_features(node_id, weather_df, now))
        
        
        # Operational features (defaults)
        features.update(self._compute_operational_features(node))
        
        return features
    
    def _compute_news_features(self, node_id: str, news_df: pd.DataFrame, now: datetime) -> Dict[str, Any]:
        """Compute news-related features."""
        features = {}
        
        if news_df.empty:
            features.update({
                'news_count_1d': 0,
                'news_count_7d': 0,
                'neg_tone_frac_3d': 0.0,
                'news_velocity': 0.0
            })
            return features
        
        # Filter news for this node
        node_news = news_df[news_df['node_id'] == node_id].copy()
        
        if node_news.empty:
            features.update({
                'news_count_1d': 0,
                'news_count_7d': 0,
                'neg_tone_frac_3d': 0.0,
                'news_velocity': 0.0
            })
            return features
        
        # News counts
        news_1d = window_count(node_news, now, hours=24)
        news_7d = window_count(node_news, now, days=7)
        
        features['news_count_1d'] = news_1d['count'].iloc[0] if not news_1d.empty else 0
        features['news_count_7d'] = news_7d['count'].iloc[0] if not news_7d.empty else 0
        
        # Negative tone fraction
        neg_frac = neg_fraction(node_news, hours=72)
        features['neg_tone_frac_3d'] = neg_frac['neg_frac'].iloc[0] if not neg_frac.empty else 0.0
        
        # News velocity
        velocity = news_velocity(node_news, baseline_days=30)
        features['news_velocity'] = velocity['news_velocity'].iloc[0] if not velocity.empty else 0.0
        
        return features
    
    def _compute_social_features(self, node_id: str, social_df: pd.DataFrame, now: datetime) -> Dict[str, Any]:
        """Compute social media features."""
        # For now, social features are combined with news features
        # This could be extended to include separate social sentiment, engagement, etc.
        return {}
    
    def _compute_event_features(self, node_id: str, events_df: pd.DataFrame, now: datetime) -> Dict[str, Any]:
        """Compute event-related features."""
        features = {}
        
        if events_df.empty:
            features['strike_flag_7d'] = 0
            return features
        
        # Filter events for this node
        node_events = events_df[events_df['node_id'] == node_id].copy()
        
        if node_events.empty:
            features['strike_flag_7d'] = 0
            return features
        
        # Strike flag
        strike_flags = strike_flag_7d(node_events, days=7)
        features['strike_flag_7d'] = strike_flags['strike_flag'].iloc[0] if not strike_flags.empty else 0
        
        return features
    
    def _compute_weather_features(self, node_id: str, weather_df: pd.DataFrame, now: datetime) -> Dict[str, Any]:
        """Compute weather-related features."""
        features = {}
        
        if weather_df.empty:
            features['weather_anomaly_7d'] = 0
            return features
        
        # Filter weather for this node
        node_weather = weather_df[weather_df['node_id'] == node_id].copy()
        
        if node_weather.empty:
            features['weather_anomaly_7d'] = 0
            return features
        
        # Weather anomaly flag
        weather_flags = weather_flag(node_weather, days=7)
        features['weather_anomaly_7d'] = weather_flags['weather_flag'].iloc[0] if not weather_flags.empty else 0
        
        return features
    
    
    def _compute_operational_features(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """Compute operational features (defaults for now)."""
        return {
            'avg_lead_time_days': None,  # Would need operational data
            'inventory_days': None,      # Would need operational data
            'single_sourced': 0,         # Default assumption
            'past_delay_days': 0,        # Default assumption
            'disruption_within_7d': None,  # Target variable - would need labels
            'days_to_disruption': None   # Target variable - would need labels
        }
    
    def _ensure_schema(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure DataFrame has the correct schema and types."""
        # Define the expected schema
        schema = {
            'node_id': str,
            'node_type': str,
            'name': str,
            'country': str,
            'lat': float,
            'lon': float,
            'tier': float,
            'news_count_1d': int,
            'news_count_7d': int,
            'neg_tone_frac_3d': float,
            'weather_anomaly_7d': int,
            'strike_flag_7d': int,
            'avg_lead_time_days': float,
            'inventory_days': float,
            'single_sourced': int,
            'past_delay_days': int,
            'news_velocity': float,
            'disruption_within_7d': int,
            'days_to_disruption': int
        }
        
        # Ensure all columns exist
        for col, dtype in schema.items():
            if col not in df.columns:
                if dtype == int:
                    df[col] = 0
                elif dtype == float:
                    df[col] = 0.0
                elif dtype == str:
                    df[col] = ''
        
        # Convert types
        for col, dtype in schema.items():
            if col in df.columns:
                try:
                    if dtype == int:
                        df[col] = df[col].fillna(0).astype(int)
                    elif dtype == float:
                        df[col] = df[col].fillna(0.0).astype(float)
                    elif dtype == str:
                        df[col] = df[col].fillna('').astype(str)
                except Exception as e:
                    logger.warning(f"Failed to convert column {col} to {dtype}: {e}")
        
        # Ensure binary flags are 0 or 1
        binary_flags = ['weather_anomaly_7d', 'strike_flag_7d', 'single_sourced', 'disruption_within_7d']
        for flag in binary_flags:
            if flag in df.columns:
                df[flag] = df[flag].clip(0, 1).astype(int)
        
        # Ensure negative tone fraction is between 0 and 1
        if 'neg_tone_frac_3d' in df.columns:
            df['neg_tone_frac_3d'] = df['neg_tone_frac_3d'].clip(0, 1)
        
        return df


def main():
    """Main function for running the feature agent."""
    # Load nodes
    nodes = read_json("data/outputs/nodes.json")
    
    agent = FeatureAgent()
    df = agent.run(nodes)
    print(f"Feature agent completed. Built features for {len(df)} nodes.")
    print(f"Features shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")


if __name__ == "__main__":
    main()
