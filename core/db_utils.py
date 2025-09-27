"""
Database utility functions and helpers.
"""
import asyncio
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from .database import get_database, check_database_health
from .db_models import get_models, DatabaseModels
from .models import Node, NewsEvent, SocialEvent, ExtractedEvent, WeatherAnomaly, MarketSignal, FeatureRow
import logging

logger = logging.getLogger(__name__)


class DatabaseUtils:
    """Database utility functions."""
    
    def __init__(self, models: DatabaseModels):
        self.models = models
        
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive database health check."""
        try:
            # Basic connection check
            health = await check_database_health()
            
            # Collection counts
            collections_info = {}
            collections = [
                'nodes', 'news_events', 'social_events', 'extracted_events',
                'weather_anomalies', 'market_signals', 'feature_rows', 'region_configs'
            ]
            
            for collection_name in collections:
                try:
                    count = await self.models.db[collection_name].count_documents({})
                    collections_info[collection_name] = {
                        "count": count,
                        "status": "healthy"
                    }
                except Exception as e:
                    collections_info[collection_name] = {
                        "count": 0,
                        "status": "error",
                        "error": str(e)
                    }
            
            health["collections"] = collections_info
            return health
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics."""
        try:
            stats = {}
            
            # Collection statistics
            collections = [
                'nodes', 'news_events', 'social_events', 'extracted_events',
                'weather_anomalies', 'market_signals', 'feature_rows', 'region_configs'
            ]
            
            for collection_name in collections:
                collection = self.models.db[collection_name]
                count = await collection.count_documents({})
                
                # Get recent activity (last 24 hours)
                yesterday = datetime.utcnow() - timedelta(days=1)
                recent_count = await collection.count_documents({
                    "created_at": {"$gte": yesterday}
                })
                
                stats[collection_name] = {
                    "total_documents": count,
                    "recent_documents_24h": recent_count
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {"error": str(e)}
    
    async def cleanup_old_data(self, days_to_keep: int = 30) -> Dict[str, int]:
        """Clean up old data beyond specified days."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            cleanup_results = {}
            
            # Clean up old news events
            news_deleted = await self.models.news_events.collection.delete_many({
                "ts": {"$lt": cutoff_date}
            })
            cleanup_results["news_events"] = news_deleted.deleted_count
            
            # Clean up old social events
            social_deleted = await self.models.social_events.collection.delete_many({
                "ts": {"$lt": cutoff_date}
            })
            cleanup_results["social_events"] = social_deleted.deleted_count
            
            # Clean up old extracted events
            extracted_deleted = await self.models.extracted_events.collection.delete_many({
                "ts_event": {"$lt": cutoff_date}
            })
            cleanup_results["extracted_events"] = extracted_deleted.deleted_count
            
            # Clean up old weather anomalies
            weather_deleted = await self.models.weather_anomalies.collection.delete_many({
                "ts": {"$lt": cutoff_date}
            })
            cleanup_results["weather_anomalies"] = weather_deleted.deleted_count
            
            # Clean up old market signals
            market_deleted = await self.models.market_signals.collection.delete_many({
                "ts": {"$lt": cutoff_date}
            })
            cleanup_results["market_signals"] = market_deleted.deleted_count
            
            logger.info(f"Cleanup completed: {cleanup_results}")
            return cleanup_results
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return {"error": str(e)}
    
    async def backup_collection(self, collection_name: str) -> Dict[str, Any]:
        """Create a backup of a collection."""
        try:
            collection = self.models.db[collection_name]
            documents = await collection.find({}).to_list(length=None)
            
            backup_data = {
                "collection_name": collection_name,
                "backup_timestamp": datetime.utcnow(),
                "document_count": len(documents),
                "documents": documents
            }
            
            # Store backup in a backup collection
            backup_collection_name = f"{collection_name}_backup"
            backup_collection = self.models.db[backup_collection_name]
            result = await backup_collection.insert_one(backup_data)
            
            return {
                "status": "success",
                "backup_id": str(result.inserted_id),
                "document_count": len(documents),
                "backup_collection": backup_collection_name
            }
            
        except Exception as e:
            logger.error(f"Error creating backup for {collection_name}: {e}")
            return {"status": "error", "error": str(e)}
    
    async def restore_collection(self, collection_name: str, backup_id: str) -> Dict[str, Any]:
        """Restore a collection from backup."""
        try:
            backup_collection_name = f"{collection_name}_backup"
            backup_collection = self.models.db[backup_collection_name]
            
            # Get backup data
            backup_data = await backup_collection.find_one({"_id": backup_id})
            if not backup_data:
                return {"status": "error", "error": "Backup not found"}
            
            # Clear existing collection
            target_collection = self.models.db[collection_name]
            await target_collection.delete_many({})
            
            # Restore documents
            if backup_data.get("documents"):
                await target_collection.insert_many(backup_data["documents"])
            
            return {
                "status": "success",
                "restored_documents": len(backup_data.get("documents", [])),
                "backup_timestamp": backup_data.get("backup_timestamp")
            }
            
        except Exception as e:
            logger.error(f"Error restoring {collection_name}: {e}")
            return {"status": "error", "error": str(e)}


class DataMigrationUtils:
    """Utilities for data migration and transformation."""
    
    def __init__(self, models: DatabaseModels):
        self.models = models
    
    async def migrate_csv_to_mongodb(self, csv_file_path: str, collection_name: str) -> Dict[str, Any]:
        """Migrate CSV data to MongoDB collection."""
        try:
            import pandas as pd
            
            # Read CSV
            df = pd.read_csv(csv_file_path)
            
            # Convert to list of dictionaries
            documents = df.to_dict('records')
            
            # Add timestamps
            now = datetime.utcnow()
            for doc in documents:
                doc["migrated_at"] = now
            
            # Insert into collection
            collection = self.models.db[collection_name]
            result = await collection.insert_many(documents)
            
            return {
                "status": "success",
                "migrated_documents": len(result.inserted_ids),
                "collection": collection_name
            }
            
        except Exception as e:
            logger.error(f"Error migrating CSV to MongoDB: {e}")
            return {"status": "error", "error": str(e)}
    
    async def export_collection_to_csv(self, collection_name: str, output_file: str) -> Dict[str, Any]:
        """Export MongoDB collection to CSV."""
        try:
            import pandas as pd
            
            # Get all documents
            collection = self.models.db[collection_name]
            documents = await collection.find({}).to_list(length=None)
            
            if not documents:
                return {"status": "error", "error": "No documents found"}
            
            # Convert to DataFrame
            df = pd.DataFrame(documents)
            
            # Remove MongoDB _id field if present
            if '_id' in df.columns:
                df = df.drop('_id', axis=1)
            
            # Save to CSV
            df.to_csv(output_file, index=False)
            
            return {
                "status": "success",
                "exported_documents": len(documents),
                "output_file": output_file
            }
            
        except Exception as e:
            logger.error(f"Error exporting collection to CSV: {e}")
            return {"status": "error", "error": str(e)}


class QueryBuilder:
    """Query builder for complex database queries."""
    
    @staticmethod
    def build_time_range_query(start_date: datetime, end_date: datetime, date_field: str = "ts") -> Dict[str, Any]:
        """Build time range query."""
        return {
            date_field: {
                "$gte": start_date,
                "$lte": end_date
            }
        }
    
    @staticmethod
    def build_sentiment_query(min_score: float = None, max_score: float = None) -> Dict[str, Any]:
        """Build sentiment score query."""
        query = {}
        if min_score is not None or max_score is not None:
            sentiment_range = {}
            if min_score is not None:
                sentiment_range["$gte"] = min_score
            if max_score is not None:
                sentiment_range["$lte"] = max_score
            query["sentiment_score"] = sentiment_range
        return query
    
    @staticmethod
    def build_geographic_query(lat: float, lon: float, radius_km: float = 50) -> Dict[str, Any]:
        """Build geographic proximity query."""
        # This is a simplified version - for production, consider using MongoDB's geospatial features
        return {
            "lat": {"$gte": lat - radius_km/111, "$lte": lat + radius_km/111},
            "lon": {"$gte": lon - radius_km/111, "$lte": lon + radius_km/111}
        }
    
    @staticmethod
    def build_aggregation_pipeline(group_by: str, date_field: str = "ts", time_window: str = "day") -> List[Dict[str, Any]]:
        """Build aggregation pipeline for time-series data."""
        pipeline = []
        
        # Date grouping
        if time_window == "day":
            date_format = "%Y-%m-%d"
        elif time_window == "hour":
            date_format = "%Y-%m-%d-%H"
        else:
            date_format = "%Y-%m-%d"
        
        pipeline.extend([
            {
                "$group": {
                    "_id": {
                        "group": f"${group_by}",
                        "date": {
                            "$dateToString": {
                                "format": date_format,
                                "date": f"${date_field}"
                            }
                        }
                    },
                    "count": {"$sum": 1},
                    "avg_sentiment": {"$avg": "$sentiment_score"},
                    "max_sentiment": {"$max": "$sentiment_score"},
                    "min_sentiment": {"$min": "$sentiment_score"}
                }
            },
            {
                "$sort": {"_id.date": 1}
            }
        ])
        
        return pipeline


# Global utility instances
async def get_db_utils() -> DatabaseUtils:
    """Get database utils instance."""
    models = await get_models()
    return DatabaseUtils(models)


async def get_migration_utils() -> DataMigrationUtils:
    """Get migration utils instance."""
    models = await get_models()
    return DataMigrationUtils(models)
