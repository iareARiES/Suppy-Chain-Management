"""
MongoDB schemas and database operations for the supply chain risk analysis system.
"""
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ASCENDING, DESCENDING, TEXT
import logging

logger = logging.getLogger(__name__)


class BaseSchema:
    """Base schema class for MongoDB operations."""
    
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection
    
    async def create_indexes(self):
        """Create indexes for the collection."""
        pass
    
    async def insert_one(self, document: Dict[str, Any]) -> str:
        """Insert a single document."""
        result = await self.collection.insert_one(document)
        return str(result.inserted_id)
    
    async def insert_many(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Insert multiple documents."""
        result = await self.collection.insert_many(documents)
        return [str(id) for id in result.inserted_ids]
    
    async def find_one(self, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single document."""
        return await self.collection.find_one(filter_dict)
    
    async def find_many(self, filter_dict: Dict[str, Any] = None, limit: int = None, 
                       sort: List[tuple] = None) -> List[Dict[str, Any]]:
        """Find multiple documents."""
        cursor = self.collection.find(filter_dict or {})
        
        if sort:
            cursor = cursor.sort(sort)
        
        if limit:
            cursor = cursor.limit(limit)
        
        return await cursor.to_list(length=None)
    
    async def update_one(self, filter_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> bool:
        """Update a single document."""
        result = await self.collection.update_one(filter_dict, update_dict)
        return result.modified_count > 0
    
    async def delete_one(self, filter_dict: Dict[str, Any]) -> bool:
        """Delete a single document."""
        result = await self.collection.delete_one(filter_dict)
        return result.deleted_count > 0
    
    async def count_documents(self, filter_dict: Dict[str, Any] = None) -> int:
        """Count documents."""
        return await self.collection.count_documents(filter_dict or {})


class NodeSchema(BaseSchema):
    """Schema for node collection."""
    
    async def create_indexes(self):
        """Create indexes for nodes collection."""
        try:
            # Unique index on node_id
            await self.collection.create_index("node_id", unique=True)
            
            # Indexes for common queries
            await self.collection.create_index("country")
            await self.collection.create_index("node_type")
            await self.collection.create_index("tier")
            await self.collection.create_index([("lat", ASCENDING), ("lon", ASCENDING)])
            
            # Text search index
            await self.collection.create_index([("name", TEXT), ("country", TEXT)])
            
            logger.info("Node indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating node indexes: {e}")
    
    async def upsert_node(self, node_data: Dict[str, Any]) -> str:
        """Upsert a node (insert or update)."""
        filter_dict = {"node_id": node_data["node_id"]}
        update_dict = {"$set": node_data}
        
        result = await self.collection.update_one(filter_dict, update_dict, upsert=True)
        
        if result.upserted_id:
            return str(result.upserted_id)
        else:
            # Find the existing document
            doc = await self.collection.find_one(filter_dict)
            return str(doc["_id"])
    
    async def find_by_node_id(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Find node by node_id."""
        return await self.find_one({"node_id": node_id})
    
    async def find_by_country(self, country: str) -> List[Dict[str, Any]]:
        """Find nodes by country."""
        return await self.find_many({"country": country})
    
    async def find_by_region(self, region: str) -> List[Dict[str, Any]]:
        """Find nodes by region."""
        return await self.find_many({"region": region})
    
    async def search_nodes(self, search_term: str) -> List[Dict[str, Any]]:
        """Search nodes by name or country."""
        filter_dict = {"$text": {"$search": search_term}}
        return await self.find_many(filter_dict)


class NewsEventSchema(BaseSchema):
    """Schema for news events collection."""
    
    async def create_indexes(self):
        """Create indexes for news events collection."""
        try:
            # Indexes for common queries
            await self.collection.create_index("node_id")
            await self.collection.create_index([("ts", DESCENDING)])
            await self.collection.create_index("outlet")
            await self.collection.create_index("sentiment_score")
            await self.collection.create_index([("ts_ingested", DESCENDING)])
            
            # Unique index on URL
            await self.collection.create_index("url", unique=True)
            
            # Text search index
            await self.collection.create_index([("headline", TEXT), ("snippet", TEXT)])
            
            # Compound indexes
            await self.collection.create_index([("node_id", ASCENDING), ("ts", DESCENDING)])
            
            logger.info("News event indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating news event indexes: {e}")
    
    async def find_by_node_id(self, node_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """Find news events by node_id."""
        sort = [("ts", DESCENDING)]
        return await self.find_many({"node_id": node_id}, limit=limit, sort=sort)
    
    async def find_recent_events(self, days: int = 7, limit: int = None) -> List[Dict[str, Any]]:
        """Find recent news events."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        filter_dict = {"ts": {"$gte": cutoff_date}}
        sort = [("ts", DESCENDING)]
        return await self.find_many(filter_dict, limit=limit, sort=sort)
    
    async def find_by_sentiment_range(self, min_score: float, max_score: float) -> List[Dict[str, Any]]:
        """Find events within sentiment range."""
        filter_dict = {
            "sentiment_score": {"$gte": min_score, "$lte": max_score}
        }
        sort = [("ts", DESCENDING)]
        return await self.find_many(filter_dict, sort=sort)
    
    async def search_events(self, search_term: str) -> List[Dict[str, Any]]:
        """Search events by headline or snippet."""
        filter_dict = {"$text": {"$search": search_term}}
        sort = [("ts", DESCENDING)]
        return await self.find_many(filter_dict, sort=sort)


class SocialEventSchema(BaseSchema):
    """Schema for social events collection."""
    
    async def create_indexes(self):
        """Create indexes for social events collection."""
        try:
            # Indexes for common queries
            await self.collection.create_index("node_id")
            await self.collection.create_index([("ts", DESCENDING)])
            await self.collection.create_index("handle")
            await self.collection.create_index("sentiment_score")
            await self.collection.create_index("engagement_count")
            await self.collection.create_index([("ts_ingested", DESCENDING)])
            
            # Text search index
            await self.collection.create_index([("text", TEXT)])
            
            # Compound indexes
            await self.collection.create_index([("node_id", ASCENDING), ("ts", DESCENDING)])
            
            logger.info("Social event indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating social event indexes: {e}")
    
    async def find_by_node_id(self, node_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """Find social events by node_id."""
        sort = [("ts", DESCENDING)]
        return await self.find_many({"node_id": node_id}, limit=limit, sort=sort)
    
    async def find_by_handle(self, handle: str) -> List[Dict[str, Any]]:
        """Find events by handle."""
        sort = [("ts", DESCENDING)]
        return await self.find_many({"handle": handle}, sort=sort)
    
    async def find_high_engagement(self, min_engagement: int = 100) -> List[Dict[str, Any]]:
        """Find events with high engagement."""
        filter_dict = {"engagement_count": {"$gte": min_engagement}}
        sort = [("engagement_count", DESCENDING)]
        return await self.find_many(filter_dict, sort=sort)


class ExtractedEventSchema(BaseSchema):
    """Schema for extracted events collection."""
    
    async def create_indexes(self):
        """Create indexes for extracted events collection."""
        try:
            # Indexes for common queries
            await self.collection.create_index("node_id")
            await self.collection.create_index("event_type")
            await self.collection.create_index([("ts_event", DESCENDING)])
            await self.collection.create_index("severity")
            await self.collection.create_index("confidence")
            await self.collection.create_index("source_url")
            
            # Text search index
            await self.collection.create_index([("extracted_text", TEXT)])
            
            # Compound indexes
            await self.collection.create_index([("node_id", ASCENDING), ("event_type", ASCENDING)])
            await self.collection.create_index([("node_id", ASCENDING), ("ts_event", DESCENDING)])
            
            logger.info("Extracted event indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating extracted event indexes: {e}")
    
    async def find_by_node_id(self, node_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """Find extracted events by node_id."""
        sort = [("ts_event", DESCENDING)]
        return await self.find_many({"node_id": node_id}, limit=limit, sort=sort)
    
    async def find_by_event_type(self, event_type: str) -> List[Dict[str, Any]]:
        """Find events by type."""
        sort = [("ts_event", DESCENDING)]
        return await self.find_many({"event_type": event_type}, sort=sort)
    
    async def find_by_severity(self, severity: str) -> List[Dict[str, Any]]:
        """Find events by severity."""
        sort = [("ts_event", DESCENDING)]
        return await self.find_many({"severity": severity}, sort=sort)
    
    async def find_high_confidence(self, min_confidence: float = 0.8) -> List[Dict[str, Any]]:
        """Find events with high confidence."""
        filter_dict = {"confidence": {"$gte": min_confidence}}
        sort = [("confidence", DESCENDING)]
        return await self.find_many(filter_dict, sort=sort)


class WeatherAnomalySchema(BaseSchema):
    """Schema for weather anomalies collection."""
    
    async def create_indexes(self):
        """Create indexes for weather anomalies collection."""
        try:
            # Indexes for common queries
            await self.collection.create_index("node_id")
            await self.collection.create_index([("ts", DESCENDING)])
            await self.collection.create_index("anomaly_type")
            await self.collection.create_index("severity")
            
            # Compound indexes
            await self.collection.create_index([("node_id", ASCENDING), ("anomaly_type", ASCENDING)])
            await self.collection.create_index([("node_id", ASCENDING), ("ts", DESCENDING)])
            
            logger.info("Weather anomaly indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating weather anomaly indexes: {e}")
    
    async def find_by_node_id(self, node_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """Find weather anomalies by node_id."""
        sort = [("ts", DESCENDING)]
        return await self.find_many({"node_id": node_id}, limit=limit, sort=sort)
    
    async def find_by_anomaly_type(self, anomaly_type: str) -> List[Dict[str, Any]]:
        """Find anomalies by type."""
        sort = [("ts", DESCENDING)]
        return await self.find_many({"anomaly_type": anomaly_type}, sort=sort)
    
    async def find_by_severity(self, severity: str) -> List[Dict[str, Any]]:
        """Find anomalies by severity."""
        sort = [("ts", DESCENDING)]
        return await self.find_many({"severity": severity}, sort=sort)


class MarketSignalSchema(BaseSchema):
    """Schema for market signals collection."""
    
    async def create_indexes(self):
        """Create indexes for market signals collection."""
        try:
            # Indexes for common queries
            await self.collection.create_index("node_id")
            await self.collection.create_index("ticker")
            await self.collection.create_index([("ts", DESCENDING)])
            await self.collection.create_index("signal_type")
            
            # Compound indexes
            await self.collection.create_index([("node_id", ASCENDING), ("signal_type", ASCENDING)])
            await self.collection.create_index([("ticker", ASCENDING), ("ts", DESCENDING)])
            
            logger.info("Market signal indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating market signal indexes: {e}")
    
    async def find_by_node_id(self, node_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """Find market signals by node_id."""
        sort = [("ts", DESCENDING)]
        return await self.find_many({"node_id": node_id}, limit=limit, sort=sort)
    
    async def find_by_ticker(self, ticker: str) -> List[Dict[str, Any]]:
        """Find signals by ticker."""
        sort = [("ts", DESCENDING)]
        return await self.find_many({"ticker": ticker}, sort=sort)
    
    async def find_by_signal_type(self, signal_type: str) -> List[Dict[str, Any]]:
        """Find signals by type."""
        sort = [("ts", DESCENDING)]
        return await self.find_many({"signal_type": signal_type}, sort=sort)


class FeatureRowSchema(BaseSchema):
    """Schema for feature rows collection."""
    
    async def create_indexes(self):
        """Create indexes for feature rows collection."""
        try:
            # Unique index on node_id
            await self.collection.create_index("node_id", unique=True)
            
            # Indexes for common queries
            await self.collection.create_index("country")
            await self.collection.create_index("node_type")
            await self.collection.create_index("tier")
            await self.collection.create_index("disruption_within_7d")
            await self.collection.create_index([("news_velocity", DESCENDING)])
            
            # Text search index
            await self.collection.create_index([("name", TEXT), ("country", TEXT)])
            
            logger.info("Feature row indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating feature row indexes: {e}")
    
    async def upsert_feature_row(self, feature_data: Dict[str, Any]) -> str:
        """Upsert a feature row (insert or update)."""
        filter_dict = {"node_id": feature_data["node_id"]}
        update_dict = {"$set": feature_data}
        
        result = await self.collection.update_one(filter_dict, update_dict, upsert=True)
        
        if result.upserted_id:
            return str(result.upserted_id)
        else:
            # Find the existing document
            doc = await self.collection.find_one(filter_dict)
            return str(doc["_id"])
    
    async def find_by_node_id(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Find feature row by node_id."""
        return await self.find_one({"node_id": node_id})
    
    async def find_high_risk_nodes(self, min_velocity: float = 0.5) -> List[Dict[str, Any]]:
        """Find nodes with high news velocity."""
        filter_dict = {"news_velocity": {"$gte": min_velocity}}
        sort = [("news_velocity", DESCENDING)]
        return await self.find_many(filter_dict, sort=sort)
    
    async def find_disruption_flagged(self) -> List[Dict[str, Any]]:
        """Find nodes flagged for potential disruption."""
        filter_dict = {"disruption_within_7d": 1}
        sort = [("news_velocity", DESCENDING)]
        return await self.find_many(filter_dict, sort=sort)


class RegionConfigSchema(BaseSchema):
    """Schema for region configs collection."""
    
    async def create_indexes(self):
        """Create indexes for region configs collection."""
        try:
            # Unique index on name
            await self.collection.create_index("name", unique=True)
            
            # Text search index
            await self.collection.create_index([("name", TEXT)])
            
            logger.info("Region config indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating region config indexes: {e}")
    
    async def upsert_region_config(self, config_data: Dict[str, Any]) -> str:
        """Upsert a region config (insert or update)."""
        filter_dict = {"name": config_data["name"]}
        update_dict = {"$set": config_data}
        
        result = await self.collection.update_one(filter_dict, update_dict, upsert=True)
        
        if result.upserted_id:
            return str(result.upserted_id)
        else:
            # Find the existing document
            doc = await self.collection.find_one(filter_dict)
            return str(doc["_id"])
    
    async def find_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find region config by name."""
        return await self.find_one({"name": name})