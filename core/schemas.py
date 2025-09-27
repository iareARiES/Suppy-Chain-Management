"""
MongoDB schemas using Motor (async MongoDB driver) with Mongoose-like functionality.
"""
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import IndexModel, ASCENDING, DESCENDING, TEXT
from pymongo.errors import DuplicateKeyError
import logging

logger = logging.getLogger(__name__)


class BaseSchema:
    """Base schema class with common functionality."""
    
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection
        
    async def create_indexes(self):
        """Create indexes for the collection. Override in subclasses."""
        pass
        
    async def find_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Find document by ID."""
        return await self.collection.find_one({"_id": document_id})
        
    async def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find one document matching query."""
        return await self.collection.find_one(query)
        
    async def find_many(self, query: Dict[str, Any] = None, limit: int = None, skip: int = None) -> List[Dict[str, Any]]:
        """Find multiple documents matching query."""
        cursor = self.collection.find(query or {})
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        return await cursor.to_list(length=limit)
        
    async def insert_one(self, document: Dict[str, Any]) -> str:
        """Insert one document and return its ID."""
        result = await self.collection.insert_one(document)
        return str(result.inserted_id)
        
    async def insert_many(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Insert multiple documents and return their IDs."""
        result = await self.collection.insert_many(documents)
        return [str(id) for id in result.inserted_ids]
        
    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any], upsert: bool = False) -> bool:
        """Update one document."""
        result = await self.collection.update_one(query, update, upsert=upsert)
        return result.modified_count > 0 or result.upserted_id is not None
        
    async def update_many(self, query: Dict[str, Any], update: Dict[str, Any]) -> int:
        """Update multiple documents."""
        result = await self.collection.update_many(query, update)
        return result.modified_count
        
    async def delete_one(self, query: Dict[str, Any]) -> bool:
        """Delete one document."""
        result = await self.collection.delete_one(query)
        return result.deleted_count > 0
        
    async def delete_many(self, query: Dict[str, Any]) -> int:
        """Delete multiple documents."""
        result = await self.collection.delete_many(query)
        return result.deleted_count
        
    async def count_documents(self, query: Dict[str, Any] = None) -> int:
        """Count documents matching query."""
        return await self.collection.count_documents(query or {})


class NodeSchema(BaseSchema):
    """Schema for supply chain nodes."""
    
    async def create_indexes(self):
        """Create indexes for nodes collection."""
        indexes = [
            IndexModel([("node_id", ASCENDING)], unique=True),
            IndexModel([("country", ASCENDING)]),
            IndexModel([("node_type", ASCENDING)]),
            IndexModel([("tier", ASCENDING)]),
            IndexModel([("lat", ASCENDING), ("lon", ASCENDING)]),
            IndexModel([("name", TEXT), ("country", TEXT)])
        ]
        await self.collection.create_indexes(indexes)
        logger.info("Created indexes for nodes collection")
        
    async def find_by_node_id(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Find node by node_id."""
        return await self.find_one({"node_id": node_id})
        
    async def find_by_country(self, country: str) -> List[Dict[str, Any]]:
        """Find all nodes in a country."""
        return await self.find_many({"country": country})
        
    async def find_by_region(self, region: str) -> List[Dict[str, Any]]:
        """Find all nodes in a region."""
        return await self.find_many({"region": region})
        
    async def find_by_tier(self, tier: float) -> List[Dict[str, Any]]:
        """Find all nodes by tier."""
        return await self.find_many({"tier": tier})
        
    async def search_nodes(self, search_term: str) -> List[Dict[str, Any]]:
        """Search nodes by name or country."""
        query = {"$text": {"$search": search_term}}
        return await self.find_many(query)
        
    async def upsert_node(self, node_data: Dict[str, Any]) -> str:
        """Insert or update a node."""
        node_id = node_data.get("node_id")
        if not node_id:
            raise ValueError("node_id is required")
            
        # Add timestamps
        now = datetime.utcnow()
        node_data["updated_at"] = now
        
        result = await self.collection.update_one(
            {"node_id": node_id},
            {"$set": node_data, "$setOnInsert": {"created_at": now}},
            upsert=True
        )
        
        if result.upserted_id:
            return str(result.upserted_id)
        else:
            # Return the existing document's _id
            existing = await self.find_by_node_id(node_id)
            return existing["_id"] if existing else None


class NewsEventSchema(BaseSchema):
    """Schema for news events."""
    
    async def create_indexes(self):
        """Create indexes for news events collection."""
        indexes = [
            IndexModel([("node_id", ASCENDING)]),
            IndexModel([("ts", DESCENDING)]),
            IndexModel([("outlet", ASCENDING)]),
            IndexModel([("sentiment_score", ASCENDING)]),
            IndexModel([("ts_ingested", DESCENDING)]),
            IndexModel([("url", ASCENDING)], unique=True),
            IndexModel([("headline", TEXT), ("snippet", TEXT)]),
            IndexModel([("node_id", ASCENDING), ("ts", DESCENDING)])
        ]
        await self.collection.create_indexes(indexes)
        logger.info("Created indexes for news_events collection")
        
    async def find_by_node_id(self, node_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """Find news events for a specific node."""
        return await self.find_many({"node_id": node_id}, limit=limit)
        
    async def find_recent_events(self, days: int = 7, limit: int = None) -> List[Dict[str, Any]]:
        """Find recent news events."""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = {"ts": {"$gte": cutoff_date}}
        return await self.find_many(query, limit=limit)
        
    async def get_recent(self, days: int = 7, limit: int = None) -> List[Dict[str, Any]]:
        """Alias for find_recent_events for backward compatibility."""
        return await self.find_recent_events(days=days, limit=limit)
        
    async def find_by_sentiment_range(self, min_score: float, max_score: float) -> List[Dict[str, Any]]:
        """Find events within sentiment score range."""
        query = {"sentiment_score": {"$gte": min_score, "$lte": max_score}}
        return await self.find_many(query)
        
    async def find_by_outlet(self, outlet: str) -> List[Dict[str, Any]]:
        """Find events from specific outlet."""
        return await self.find_many({"outlet": outlet})
        
    async def search_events(self, search_term: str) -> List[Dict[str, Any]]:
        """Search events by headline or snippet."""
        query = {"$text": {"$search": search_term}}
        return await self.find_many(query)


class SocialEventSchema(BaseSchema):
    """Schema for social media events."""
    
    async def create_indexes(self):
        """Create indexes for social events collection."""
        indexes = [
            IndexModel([("node_id", ASCENDING)]),
            IndexModel([("ts", DESCENDING)]),
            IndexModel([("handle", ASCENDING)]),
            IndexModel([("sentiment_score", ASCENDING)]),
            IndexModel([("engagement_count", DESCENDING)]),
            IndexModel([("ts_ingested", DESCENDING)]),
            IndexModel([("text", TEXT)]),
            IndexModel([("node_id", ASCENDING), ("ts", DESCENDING)])
        ]
        await self.collection.create_indexes(indexes)
        logger.info("Created indexes for social_events collection")
        
    async def find_by_node_id(self, node_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """Find social events for a specific node."""
        return await self.find_many({"node_id": node_id}, limit=limit)
        
    async def find_by_handle(self, handle: str) -> List[Dict[str, Any]]:
        """Find events from specific handle."""
        return await self.find_many({"handle": handle})
        
    async def find_high_engagement(self, min_engagement: int = 100) -> List[Dict[str, Any]]:
        """Find events with high engagement."""
        query = {"engagement_count": {"$gte": min_engagement}}
        return await self.find_many(query)


class ExtractedEventSchema(BaseSchema):
    """Schema for extracted events."""
    
    async def create_indexes(self):
        """Create indexes for extracted events collection."""
        indexes = [
            IndexModel([("node_id", ASCENDING)]),
            IndexModel([("event_type", ASCENDING)]),
            IndexModel([("ts_event", DESCENDING)]),
            IndexModel([("severity", ASCENDING)]),
            IndexModel([("confidence", DESCENDING)]),
            IndexModel([("source_url", ASCENDING)]),
            IndexModel([("extracted_text", TEXT)]),
            IndexModel([("node_id", ASCENDING), ("event_type", ASCENDING)]),
            IndexModel([("node_id", ASCENDING), ("ts_event", DESCENDING)])
        ]
        await self.collection.create_indexes(indexes)
        logger.info("Created indexes for extracted_events collection")
        
    async def find_by_node_id(self, node_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """Find extracted events for a specific node."""
        return await self.find_many({"node_id": node_id}, limit=limit)
        
    async def find_by_event_type(self, event_type: str) -> List[Dict[str, Any]]:
        """Find events by type."""
        return await self.find_many({"event_type": event_type})
        
    async def find_by_severity(self, severity: str) -> List[Dict[str, Any]]:
        """Find events by severity."""
        return await self.find_many({"severity": severity})
        
    async def find_high_confidence(self, min_confidence: float = 0.8) -> List[Dict[str, Any]]:
        """Find events with high confidence."""
        query = {"confidence": {"$gte": min_confidence}}
        return await self.find_many(query)


class WeatherAnomalySchema(BaseSchema):
    """Schema for weather anomalies."""
    
    async def create_indexes(self):
        """Create indexes for weather anomalies collection."""
        indexes = [
            IndexModel([("node_id", ASCENDING)]),
            IndexModel([("ts", DESCENDING)]),
            IndexModel([("anomaly_type", ASCENDING)]),
            IndexModel([("severity", ASCENDING)]),
            IndexModel([("node_id", ASCENDING), ("anomaly_type", ASCENDING)]),
            IndexModel([("node_id", ASCENDING), ("ts", DESCENDING)])
        ]
        await self.collection.create_indexes(indexes)
        logger.info("Created indexes for weather_anomalies collection")
        
    async def find_by_node_id(self, node_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """Find weather anomalies for a specific node."""
        return await self.find_many({"node_id": node_id}, limit=limit)
        
    async def find_by_anomaly_type(self, anomaly_type: str) -> List[Dict[str, Any]]:
        """Find anomalies by type."""
        return await self.find_many({"anomaly_type": anomaly_type})
        
    async def find_by_severity(self, severity: str) -> List[Dict[str, Any]]:
        """Find anomalies by severity."""
        return await self.find_many({"severity": severity})


class MarketSignalSchema(BaseSchema):
    """Schema for market signals."""
    
    async def create_indexes(self):
        """Create indexes for market signals collection."""
        indexes = [
            IndexModel([("node_id", ASCENDING)]),
            IndexModel([("ticker", ASCENDING)]),
            IndexModel([("ts", DESCENDING)]),
            IndexModel([("signal_type", ASCENDING)]),
            IndexModel([("node_id", ASCENDING), ("signal_type", ASCENDING)]),
            IndexModel([("ticker", ASCENDING), ("ts", DESCENDING)])
        ]
        await self.collection.create_indexes(indexes)
        logger.info("Created indexes for market_signals collection")
        
    async def find_by_node_id(self, node_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """Find market signals for a specific node."""
        return await self.find_many({"node_id": node_id}, limit=limit)
        
    async def find_by_ticker(self, ticker: str) -> List[Dict[str, Any]]:
        """Find signals by ticker."""
        return await self.find_many({"ticker": ticker})
        
    async def find_by_signal_type(self, signal_type: str) -> List[Dict[str, Any]]:
        """Find signals by type."""
        return await self.find_many({"signal_type": signal_type})


class FeatureRowSchema(BaseSchema):
    """Schema for feature rows."""
    
    async def create_indexes(self):
        """Create indexes for feature rows collection."""
        indexes = [
            IndexModel([("node_id", ASCENDING)], unique=True),
            IndexModel([("country", ASCENDING)]),
            IndexModel([("node_type", ASCENDING)]),
            IndexModel([("tier", ASCENDING)]),
            IndexModel([("disruption_within_7d", ASCENDING)]),
            IndexModel([("news_velocity", DESCENDING)]),
            IndexModel([("name", TEXT), ("country", TEXT)])
        ]
        await self.collection.create_indexes(indexes)
        logger.info("Created indexes for feature_rows collection")
        
    async def find_by_node_id(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Find feature row by node_id."""
        return await self.find_one({"node_id": node_id})
        
    async def find_high_risk_nodes(self, min_velocity: float = 0.5) -> List[Dict[str, Any]]:
        """Find nodes with high news velocity (potential risk)."""
        query = {"news_velocity": {"$gte": min_velocity}}
        return await self.find_many(query)
        
    async def find_disruption_flagged(self) -> List[Dict[str, Any]]:
        """Find nodes flagged for potential disruption."""
        return await self.find_many({"disruption_within_7d": 1})
        
    async def upsert_feature_row(self, feature_data: Dict[str, Any]) -> str:
        """Insert or update a feature row."""
        node_id = feature_data.get("node_id")
        if not node_id:
            raise ValueError("node_id is required")
            
        # Add timestamps
        now = datetime.utcnow()
        feature_data["updated_at"] = now
        
        result = await self.collection.update_one(
            {"node_id": node_id},
            {"$set": feature_data, "$setOnInsert": {"created_at": now}},
            upsert=True
        )
        
        if result.upserted_id:
            return str(result.upserted_id)
        else:
            # Return the existing document's _id
            existing = await self.find_by_node_id(node_id)
            return existing["_id"] if existing else None


class RegionConfigSchema(BaseSchema):
    """Schema for region configurations."""
    
    async def create_indexes(self):
        """Create indexes for region configs collection."""
        indexes = [
            IndexModel([("name", ASCENDING)], unique=True),
            IndexModel([("name", TEXT)])
        ]
        await self.collection.create_indexes(indexes)
        logger.info("Created indexes for region_configs collection")
        
    async def find_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find region config by name."""
        return await self.find_one({"name": name})
        
    async def upsert_region_config(self, config_data: Dict[str, Any]) -> str:
        """Insert or update a region configuration."""
        name = config_data.get("name")
        if not name:
            raise ValueError("name is required")
            
        # Add timestamps
        now = datetime.utcnow()
        config_data["updated_at"] = now
        
        result = await self.collection.update_one(
            {"name": name},
            {"$set": config_data, "$setOnInsert": {"created_at": now}},
            upsert=True
        )
        
        if result.upserted_id:
            return str(result.upserted_id)
        else:
            # Return the existing document's _id
            existing = await self.find_by_name(name)
            return existing["_id"] if existing else None
