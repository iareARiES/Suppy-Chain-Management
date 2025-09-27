"""
Database models that combine Pydantic models with MongoDB schemas.
"""
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from .models import (
    Node, NewsEvent, SocialEvent, ExtractedEvent, WeatherAnomaly, 
    MarketSignal, FeatureRow, RegionConfig, AllowlistConfig
)
from .schemas import (
    NodeSchema, NewsEventSchema, SocialEventSchema, ExtractedEventSchema,
    WeatherAnomalySchema, MarketSignalSchema, FeatureRowSchema, RegionConfigSchema
)
from .database import get_database
import logging

logger = logging.getLogger(__name__)


class DatabaseModels:
    """Database models manager."""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        
        # Initialize schemas
        self.nodes = NodeSchema(database.nodes)
        self.news_events = NewsEventSchema(database.news_events)
        self.social_events = SocialEventSchema(database.social_events)
        self.extracted_events = ExtractedEventSchema(database.extracted_events)
        self.weather_anomalies = WeatherAnomalySchema(database.weather_anomalies)
        self.market_signals = MarketSignalSchema(database.market_signals)
        self.feature_rows = FeatureRowSchema(database.feature_rows)
        self.region_configs = RegionConfigSchema(database.region_configs)
        
    async def initialize_indexes(self):
        """Initialize all database indexes."""
        try:
            await self.nodes.create_indexes()
            await self.news_events.create_indexes()
            await self.social_events.create_indexes()
            await self.extracted_events.create_indexes()
            await self.weather_anomalies.create_indexes()
            await self.market_signals.create_indexes()
            await self.feature_rows.create_indexes()
            await self.region_configs.create_indexes()
            logger.info("All database indexes initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database indexes: {e}")
            raise


class NodeModel:
    """Node model with database operations."""
    
    def __init__(self, schema: NodeSchema):
        self.schema = schema
        
    async def create(self, node: Node) -> str:
        """Create a new node."""
        node_data = node.dict()
        return await self.schema.upsert_node(node_data)
        
    async def get_by_id(self, node_id: str) -> Optional[Node]:
        """Get node by ID."""
        data = await self.schema.find_by_node_id(node_id)
        return Node(**data) if data else None
        
    async def get_by_country(self, country: str) -> List[Node]:
        """Get all nodes in a country."""
        data_list = await self.schema.find_by_country(country)
        return [Node(**data) for data in data_list]
        
    async def get_by_region(self, region: str) -> List[Node]:
        """Get all nodes in a region."""
        data_list = await self.schema.find_by_region(region)
        return [Node(**data) for data in data_list]
        
    async def search(self, search_term: str) -> List[Node]:
        """Search nodes by name or country."""
        data_list = await self.schema.search_nodes(search_term)
        return [Node(**data) for data in data_list]
        
    async def update(self, node_id: str, node: Node) -> bool:
        """Update a node."""
        node_data = node.dict()
        node_data["updated_at"] = datetime.utcnow()
        return await self.schema.update_one(
            {"node_id": node_id},
            {"$set": node_data}
        )
        
    async def delete(self, node_id: str) -> bool:
        """Delete a node."""
        return await self.schema.delete_one({"node_id": node_id})


class NewsEventModel:
    """News event model with database operations."""
    
    def __init__(self, schema: NewsEventSchema):
        self.schema = schema
        
    async def create(self, event: NewsEvent) -> str:
        """Create a new news event."""
        event_data = event.dict()
        return await self.schema.insert_one(event_data)
        
    async def get_by_node_id(self, node_id: str, limit: int = None) -> List[NewsEvent]:
        """Get news events for a node."""
        data_list = await self.schema.find_by_node_id(node_id, limit)
        return [NewsEvent(**data) for data in data_list]
        
    async def get_recent(self, days: int = 7, limit: int = None) -> List[NewsEvent]:
        """Get recent news events."""
        data_list = await self.schema.find_recent_events(days, limit)
        return [NewsEvent(**data) for data in data_list]
        
    async def get_by_sentiment_range(self, min_score: float, max_score: float) -> List[NewsEvent]:
        """Get events within sentiment range."""
        data_list = await self.schema.find_by_sentiment_range(min_score, max_score)
        return [NewsEvent(**data) for data in data_list]
        
    async def search(self, search_term: str) -> List[NewsEvent]:
        """Search events by headline or snippet."""
        data_list = await self.schema.search_events(search_term)
        return [NewsEvent(**data) for data in data_list]
        
    async def bulk_create(self, events: List[NewsEvent]) -> List[str]:
        """Create multiple news events."""
        events_data = [event.dict() for event in events]
        return await self.schema.insert_many(events_data)


class SocialEventModel:
    """Social event model with database operations."""
    
    def __init__(self, schema: SocialEventSchema):
        self.schema = schema
        
    async def create(self, event: SocialEvent) -> str:
        """Create a new social event."""
        event_data = event.dict()
        return await self.schema.insert_one(event_data)
        
    async def get_by_node_id(self, node_id: str, limit: int = None) -> List[SocialEvent]:
        """Get social events for a node."""
        data_list = await self.schema.find_by_node_id(node_id, limit)
        return [SocialEvent(**data) for data in data_list]
        
    async def get_by_handle(self, handle: str) -> List[SocialEvent]:
        """Get events from specific handle."""
        data_list = await self.schema.find_by_handle(handle)
        return [SocialEvent(**data) for data in data_list]
        
    async def get_high_engagement(self, min_engagement: int = 100) -> List[SocialEvent]:
        """Get events with high engagement."""
        data_list = await self.schema.find_high_engagement(min_engagement)
        return [SocialEvent(**data) for data in data_list]
        
    async def bulk_create(self, events: List[SocialEvent]) -> List[str]:
        """Create multiple social events."""
        events_data = [event.dict() for event in events]
        return await self.schema.insert_many(events_data)


class ExtractedEventModel:
    """Extracted event model with database operations."""
    
    def __init__(self, schema: ExtractedEventSchema):
        self.schema = schema
        
    async def create(self, event: ExtractedEvent) -> str:
        """Create a new extracted event."""
        event_data = event.dict()
        return await self.schema.insert_one(event_data)
        
    async def get_by_node_id(self, node_id: str, limit: int = None) -> List[ExtractedEvent]:
        """Get extracted events for a node."""
        data_list = await self.schema.find_by_node_id(node_id, limit)
        return [ExtractedEvent(**data) for data in data_list]
        
    async def get_by_event_type(self, event_type: str) -> List[ExtractedEvent]:
        """Get events by type."""
        data_list = await self.schema.find_by_event_type(event_type)
        return [ExtractedEvent(**data) for data in data_list]
        
    async def get_by_severity(self, severity: str) -> List[ExtractedEvent]:
        """Get events by severity."""
        data_list = await self.schema.find_by_severity(severity)
        return [ExtractedEvent(**data) for data in data_list]
        
    async def get_high_confidence(self, min_confidence: float = 0.8) -> List[ExtractedEvent]:
        """Get events with high confidence."""
        data_list = await self.schema.find_high_confidence(min_confidence)
        return [ExtractedEvent(**data) for data in data_list]
        
    async def bulk_create(self, events: List[ExtractedEvent]) -> List[str]:
        """Create multiple extracted events."""
        events_data = [event.dict() for event in events]
        return await self.schema.insert_many(events_data)


class WeatherAnomalyModel:
    """Weather anomaly model with database operations."""
    
    def __init__(self, schema: WeatherAnomalySchema):
        self.schema = schema
        
    async def create(self, anomaly: WeatherAnomaly) -> str:
        """Create a new weather anomaly."""
        anomaly_data = anomaly.dict()
        return await self.schema.insert_one(anomaly_data)
        
    async def get_by_node_id(self, node_id: str, limit: int = None) -> List[WeatherAnomaly]:
        """Get weather anomalies for a node."""
        data_list = await self.schema.find_by_node_id(node_id, limit)
        return [WeatherAnomaly(**data) for data in data_list]
        
    async def get_by_anomaly_type(self, anomaly_type: str) -> List[WeatherAnomaly]:
        """Get anomalies by type."""
        data_list = await self.schema.find_by_anomaly_type(anomaly_type)
        return [WeatherAnomaly(**data) for data in data_list]
        
    async def get_by_severity(self, severity: str) -> List[WeatherAnomaly]:
        """Get anomalies by severity."""
        data_list = await self.schema.find_by_severity(severity)
        return [WeatherAnomaly(**data) for data in data_list]
        
    async def bulk_create(self, anomalies: List[WeatherAnomaly]) -> List[str]:
        """Create multiple weather anomalies."""
        anomalies_data = [anomaly.dict() for anomaly in anomalies]
        return await self.schema.insert_many(anomalies_data)


class MarketSignalModel:
    """Market signal model with database operations."""
    
    def __init__(self, schema: MarketSignalSchema):
        self.schema = schema
        
    async def create(self, signal: MarketSignal) -> str:
        """Create a new market signal."""
        signal_data = signal.dict()
        return await self.schema.insert_one(signal_data)
        
    async def get_by_node_id(self, node_id: str, limit: int = None) -> List[MarketSignal]:
        """Get market signals for a node."""
        data_list = await self.schema.find_by_node_id(node_id, limit)
        return [MarketSignal(**data) for data in data_list]
        
    async def get_by_ticker(self, ticker: str) -> List[MarketSignal]:
        """Get signals by ticker."""
        data_list = await self.schema.find_by_ticker(ticker)
        return [MarketSignal(**data) for data in data_list]
        
    async def get_by_signal_type(self, signal_type: str) -> List[MarketSignal]:
        """Get signals by type."""
        data_list = await self.schema.find_by_signal_type(signal_type)
        return [MarketSignal(**data) for data in data_list]
        
    async def bulk_create(self, signals: List[MarketSignal]) -> List[str]:
        """Create multiple market signals."""
        signals_data = [signal.dict() for signal in signals]
        return await self.schema.insert_many(signals_data)


class FeatureRowModel:
    """Feature row model with database operations."""
    
    def __init__(self, schema: FeatureRowSchema):
        self.schema = schema
        
    async def create(self, feature_row: FeatureRow) -> str:
        """Create a new feature row."""
        feature_data = feature_row.dict()
        return await self.schema.upsert_feature_row(feature_data)
        
    async def get_by_node_id(self, node_id: str) -> Optional[FeatureRow]:
        """Get feature row by node ID."""
        data = await self.schema.find_by_node_id(node_id)
        return FeatureRow(**data) if data else None
        
    async def get_high_risk_nodes(self, min_velocity: float = 0.5) -> List[FeatureRow]:
        """Get nodes with high news velocity."""
        data_list = await self.schema.find_high_risk_nodes(min_velocity)
        return [FeatureRow(**data) for data in data_list]
        
    async def get_disruption_flagged(self) -> List[FeatureRow]:
        """Get nodes flagged for potential disruption."""
        data_list = await self.schema.find_disruption_flagged()
        return [FeatureRow(**data) for data in data_list]
        
    async def update(self, node_id: str, feature_row: FeatureRow) -> bool:
        """Update a feature row."""
        feature_data = feature_row.dict()
        feature_data["updated_at"] = datetime.utcnow()
        return await self.schema.update_one(
            {"node_id": node_id},
            {"$set": feature_data}
        )
        
    async def bulk_create(self, feature_rows: List[FeatureRow]) -> List[str]:
        """Create multiple feature rows."""
        results = []
        for feature_row in feature_rows:
            result = await self.create(feature_row)
            results.append(result)
        return results


class RegionConfigModel:
    """Region config model with database operations."""
    
    def __init__(self, schema: RegionConfigSchema):
        self.schema = schema
        
    async def create(self, config: RegionConfig) -> str:
        """Create a new region configuration."""
        config_data = config.dict()
        return await self.schema.upsert_region_config(config_data)
        
    async def get_by_name(self, name: str) -> Optional[RegionConfig]:
        """Get region config by name."""
        data = await self.schema.find_by_name(name)
        return RegionConfig(**data) if data else None
        
    async def get_all(self) -> List[RegionConfig]:
        """Get all region configurations."""
        data_list = await self.schema.find_many()
        return [RegionConfig(**data) for data in data_list]


# Global models instance
async def get_models() -> DatabaseModels:
    """Get database models instance."""
    database = await get_database()
    return DatabaseModels(database)
