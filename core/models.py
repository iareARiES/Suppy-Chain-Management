"""
Pydantic models for the supply chain risk analysis system.
"""
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
import pandas as pd


class Node(BaseModel):
    """Supply chain node representation."""
    node_id: str
    node_type: str = "supplier"
    name: str
    country: str
    lat: float
    lon: float
    tier: float = 1.0
    category: Optional[str] = None
    site_url: Optional[str] = None
    alt_url: Optional[str] = None
    x_handle: Optional[str] = None
    ticker: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None

    @validator('lat', 'lon')
    def validate_coordinates(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError('Coordinates must be numeric')
        return float(v)

    @classmethod
    def from_raw(cls, name: str, country: str, lat: float, lon: float, **kwargs) -> 'Node':
        """Create node from raw data."""
        # Generate node_id from name, country, and coordinates
        clean_name = name.replace(' ', '-').replace(',', '').replace('.', '').replace('(', '').replace(')', '')
        clean_country = country.replace(' ', '-')
        node_id = f"{clean_country}_{clean_name}_{lat:.2f}_{lon:.2f}"
        
        return cls(
            node_id=node_id,
            name=name,
            country=country,
            lat=lat,
            lon=lon,
            **kwargs
        )


class NewsEvent(BaseModel):
    """News event representation."""
    node_id: str
    url: str
    headline: str
    snippet: Optional[str] = None
    outlet: str
    ts: datetime
    ts_ingested: datetime = Field(default_factory=datetime.utcnow)
    sentiment_score: Optional[float] = None
    language: Optional[str] = None
    region: Optional[str] = None

    @validator('sentiment_score')
    def validate_sentiment(cls, v):
        if v is not None and not (-1 <= v <= 1):
            raise ValueError('Sentiment score must be between -1 and 1')
        return v


class SocialEvent(BaseModel):
    """Social media event representation."""
    node_id: str
    ts: datetime
    handle: str
    text: str
    url: Optional[str] = None
    ts_ingested: datetime = Field(default_factory=datetime.utcnow)
    sentiment_score: Optional[float] = None
    engagement_count: Optional[int] = None


class ExtractedEvent(BaseModel):
    """Extracted event from deep crawling."""
    node_id: str
    event_type: str  # fire, flood, strike, inspection, shutdown, outage, policy, M&A
    ts_event: datetime
    severity: Optional[str] = None  # low, medium, high
    duration_h: Optional[float] = None
    geo_text: Optional[str] = None
    source_url: str
    extracted_text: str
    confidence: Optional[float] = None

    @validator('event_type')
    def validate_event_type(cls, v):
        valid_types = {'fire', 'flood', 'strike', 'inspection', 'shutdown', 'outage', 'policy', 'M&A', 'other'}
        if v not in valid_types:
            raise ValueError(f'Event type must be one of {valid_types}')
        return v


class WeatherAnomaly(BaseModel):
    """Weather anomaly representation."""
    node_id: str
    ts: datetime
    anomaly_type: str  # heavy_precip, extreme_heat, high_wind, storm
    severity: str  # low, medium, high
    value: float  # actual measurement
    threshold: float  # threshold that was exceeded
    duration_h: Optional[float] = None

    @validator('anomaly_type')
    def validate_anomaly_type(cls, v):
        valid_types = {'heavy_precip', 'extreme_heat', 'high_wind', 'storm'}
        if v not in valid_types:
            raise ValueError(f'Anomaly type must be one of {valid_types}')
        return v


class MarketSignal(BaseModel):
    """Market signal representation."""
    node_id: str
    ticker: Optional[str] = None
    ts: datetime
    signal_type: str  # price, volume, volatility
    value: float
    z_score: Optional[float] = None  # vs 30-day baseline
    change_pct: Optional[float] = None


class FeatureRow(BaseModel):
    """Final feature row for ML pipeline."""
    node_id: str
    node_type: str = "supplier"
    name: str
    country: str
    lat: float
    lon: float
    tier: float = 1.0
    news_count_1d: int = 0
    news_count_7d: int = 0
    neg_tone_frac_3d: float = 0.0
    weather_anomaly_7d: int = 0
    strike_flag_7d: int = 0
    avg_lead_time_days: Optional[float] = None
    inventory_days: Optional[float] = None
    single_sourced: int = 0
    past_delay_days: int = 0
    news_velocity: float = 0.0
    disruption_within_7d: Optional[int] = None
    days_to_disruption: Optional[int] = None

    @validator('neg_tone_frac_3d')
    def validate_neg_tone(cls, v):
        if not (0 <= v <= 1):
            raise ValueError('Negative tone fraction must be between 0 and 1')
        return v

    @validator('weather_anomaly_7d', 'strike_flag_7d', 'single_sourced', 'disruption_within_7d')
    def validate_binary_flags(cls, v):
        if v is not None and v not in [0, 1]:
            raise ValueError('Binary flags must be 0 or 1')
        return v

    @classmethod
    def from_dataframe_row(cls, row: pd.Series) -> 'FeatureRow':
        """Create FeatureRow from pandas DataFrame row."""
        return cls(**row.to_dict())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV export."""
        return self.dict()


class RegionConfig(BaseModel):
    """Region configuration from allowlist."""
    name: str
    outlets: List[Dict[str, str]]


class AllowlistConfig(BaseModel):
    """Complete allowlist configuration."""
    regions: Dict[str, RegionConfig]

    @classmethod
    def from_yaml(cls, data: Dict[str, Any]) -> 'AllowlistConfig':
        """Create from YAML data."""
        regions = {}
        for region_key, region_data in data.get('regions', {}).items():
            regions[region_key] = RegionConfig(**region_data)
        return cls(regions=regions)
