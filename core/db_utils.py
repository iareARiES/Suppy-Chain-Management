"""
Database utility functions for the supply chain risk analysis system.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
import pandas as pd

logger = logging.getLogger(__name__)


class DatabaseUtils:
    """Utility class for database operations."""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics for all collections."""
        stats = {}
        
        collections = [
            'nodes', 'news_events', 'social_events', 'extracted_events',
            'weather_anomalies', 'market_signals', 'feature_rows', 'region_configs'
        ]
        
        for collection_name in collections:
            try:
                collection = self.db[collection_name]
                count = await collection.count_documents({})
                stats[collection_name] = {
                    'count': count,
                    'status': 'active' if count > 0 else 'empty'
                }
            except Exception as e:
                stats[collection_name] = {
                    'count': 0,
                    'status': 'error',
                    'error': str(e)
                }
        
        return stats
    
    async def cleanup_old_data(self, retention_days: Dict[str, int]) -> Dict[str, int]:
        """Clean up old data based on retention policies."""
        results = {}
        
        for collection_name, days in retention_days.items():
            if days <= 0:  # Keep forever
                continue
            
            try:
                collection = self.db[collection_name]
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                
                # Delete old documents
                result = await collection.delete_many({
                    'ts': {'$lt': cutoff_date}
                })
                
                results[collection_name] = result.deleted_count
                logger.info(f"Cleaned up {result.deleted_count} old documents from {collection_name}")
                
            except Exception as e:
                logger.error(f"Error cleaning up {collection_name}: {e}")
                results[collection_name] = 0
        
        return results
    
    async def backup_collection(self, collection_name: str, backup_path: str) -> bool:
        """Backup a collection to a file."""
        try:
            collection = self.db[collection_name]
            documents = await collection.find({}).to_list(length=None)
            
            # Convert to DataFrame and save
            if documents:
                df = pd.DataFrame(documents)
                df.to_parquet(backup_path, index=False)
                logger.info(f"Backed up {len(documents)} documents from {collection_name} to {backup_path}")
                return True
            else:
                logger.warning(f"No documents found in {collection_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error backing up {collection_name}: {e}")
            return False
    
    async def restore_collection(self, collection_name: str, backup_path: str) -> bool:
        """Restore a collection from a backup file."""
        try:
            # Load data from backup
            df = pd.read_parquet(backup_path)
            documents = df.to_dict('records')
            
            # Clear existing collection
            collection = self.db[collection_name]
            await collection.delete_many({})
            
            # Insert restored documents
            if documents:
                await collection.insert_many(documents)
                logger.info(f"Restored {len(documents)} documents to {collection_name}")
                return True
            else:
                logger.warning(f"No documents found in backup file {backup_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error restoring {collection_name}: {e}")
            return False
    
    async def get_data_quality_report(self) -> Dict[str, Any]:
        """Generate a data quality report."""
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'collections': {}
        }
        
        collections = [
            'nodes', 'news_events', 'social_events', 'extracted_events',
            'weather_anomalies', 'market_signals', 'feature_rows'
        ]
        
        for collection_name in collections:
            try:
                collection = self.db[collection_name]
                
                # Get basic stats
                total_count = await collection.count_documents({})
                
                # Get recent data count (last 7 days)
                recent_cutoff = datetime.utcnow() - timedelta(days=7)
                recent_count = await collection.count_documents({
                    'ts': {'$gte': recent_cutoff}
                })
                
                # Get null value counts for key fields
                null_counts = {}
                if collection_name == 'nodes':
                    null_counts['name'] = await collection.count_documents({'name': {'$in': [None, '']}})
                    null_counts['country'] = await collection.count_documents({'country': {'$in': [None, '']}})
                elif collection_name == 'news_events':
                    null_counts['sentiment_score'] = await collection.count_documents({'sentiment_score': None})
                    null_counts['headline'] = await collection.count_documents({'headline': {'$in': [None, '']}})
                
                report['collections'][collection_name] = {
                    'total_count': total_count,
                    'recent_count': recent_count,
                    'null_counts': null_counts,
                    'data_freshness': recent_count / total_count if total_count > 0 else 0
                }
                
            except Exception as e:
                report['collections'][collection_name] = {
                    'error': str(e)
                }
        
        return report
    
    async def optimize_indexes(self) -> Dict[str, Any]:
        """Analyze and optimize database indexes."""
        results = {}
        
        collections = [
            'nodes', 'news_events', 'social_events', 'extracted_events',
            'weather_anomalies', 'market_signals', 'feature_rows'
        ]
        
        for collection_name in collections:
            try:
                collection = self.db[collection_name]
                
                # Get index information
                indexes = await collection.list_indexes().to_list(length=None)
                
                # Analyze index usage (this would require MongoDB profiling in production)
                results[collection_name] = {
                    'index_count': len(indexes),
                    'indexes': [idx['name'] for idx in indexes],
                    'status': 'analyzed'
                }
                
            except Exception as e:
                results[collection_name] = {
                    'error': str(e)
                }
        
        return results
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get database performance metrics."""
        try:
            # Get database stats
            stats = await self.db.command("dbStats")
            
            # Get collection stats
            collection_stats = {}
            for collection_name in ['nodes', 'news_events', 'social_events', 'extracted_events']:
                try:
                    coll_stats = await self.db.command("collStats", collection_name)
                    collection_stats[collection_name] = {
                        'size': coll_stats.get('size', 0),
                        'count': coll_stats.get('count', 0),
                        'avgObjSize': coll_stats.get('avgObjSize', 0)
                    }
                except Exception as e:
                    collection_stats[collection_name] = {'error': str(e)}
            
            return {
                'database_size': stats.get('dataSize', 0),
                'storage_size': stats.get('storageSize', 0),
                'index_size': stats.get('indexSize', 0),
                'collections': collection_stats,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {'error': str(e)}


class DataValidator:
    """Data validation utilities."""
    
    @staticmethod
    def validate_node_data(node_data: Dict[str, Any]) -> List[str]:
        """Validate node data."""
        errors = []
        
        required_fields = ['node_id', 'name', 'country', 'lat', 'lon']
        for field in required_fields:
            if field not in node_data or node_data[field] is None:
                errors.append(f"Missing required field: {field}")
        
        # Validate coordinates
        if 'lat' in node_data and 'lon' in node_data:
            try:
                lat = float(node_data['lat'])
                lon = float(node_data['lon'])
                if not (-90 <= lat <= 90):
                    errors.append("Latitude must be between -90 and 90")
                if not (-180 <= lon <= 180):
                    errors.append("Longitude must be between -180 and 180")
            except (ValueError, TypeError):
                errors.append("Invalid coordinate values")
        
        # Validate tier
        if 'tier' in node_data:
            try:
                tier = float(node_data['tier'])
                if tier < 0:
                    errors.append("Tier must be non-negative")
            except (ValueError, TypeError):
                errors.append("Invalid tier value")
        
        return errors
    
    @staticmethod
    def validate_news_event_data(event_data: Dict[str, Any]) -> List[str]:
        """Validate news event data."""
        errors = []
        
        required_fields = ['node_id', 'url', 'headline', 'outlet', 'ts']
        for field in required_fields:
            if field not in event_data or event_data[field] is None:
                errors.append(f"Missing required field: {field}")
        
        # Validate URL
        if 'url' in event_data:
            url = event_data['url']
            if not isinstance(url, str) or not url.startswith(('http://', 'https://')):
                errors.append("Invalid URL format")
        
        # Validate sentiment score
        if 'sentiment_score' in event_data and event_data['sentiment_score'] is not None:
            try:
                score = float(event_data['sentiment_score'])
                if not (-1 <= score <= 1):
                    errors.append("Sentiment score must be between -1 and 1")
            except (ValueError, TypeError):
                errors.append("Invalid sentiment score")
        
        return errors
    
    @staticmethod
    def validate_feature_row_data(feature_data: Dict[str, Any]) -> List[str]:
        """Validate feature row data."""
        errors = []
        
        required_fields = ['node_id', 'name', 'country']
        for field in required_fields:
            if field not in feature_data or feature_data[field] is None:
                errors.append(f"Missing required field: {field}")
        
        # Validate numeric fields
        numeric_fields = [
            'news_count_1d', 'news_count_7d', 'neg_tone_frac_3d',
            'weather_anomaly_7d', 'strike_flag_7d', 'single_sourced',
            'past_delay_days', 'news_velocity', 'disruption_within_7d'
        ]
        
        for field in numeric_fields:
            if field in feature_data and feature_data[field] is not None:
                try:
                    value = float(feature_data[field])
                    if field in ['neg_tone_frac_3d'] and not (0 <= value <= 1):
                        errors.append(f"{field} must be between 0 and 1")
                    elif field in ['weather_anomaly_7d', 'strike_flag_7d', 'single_sourced', 'disruption_within_7d']:
                        if value not in [0, 1]:
                            errors.append(f"{field} must be 0 or 1")
                except (ValueError, TypeError):
                    errors.append(f"Invalid value for {field}")
        
        return errors


class DataAggregator:
    """Data aggregation utilities."""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
    
    async def get_supplier_risk_summary(self, node_id: str) -> Dict[str, Any]:
        """Get risk summary for a specific supplier."""
        try:
            # Get recent news events
            news_collection = self.db['news_events']
            recent_news = await news_collection.count_documents({
                'node_id': node_id,
                'ts': {'$gte': datetime.utcnow() - timedelta(days=7)}
            })
            
            # Get negative sentiment news
            negative_news = await news_collection.count_documents({
                'node_id': node_id,
                'sentiment_score': {'$lt': -0.3},
                'ts': {'$gte': datetime.utcnow() - timedelta(days=7)}
            })
            
            # Get weather anomalies
            weather_collection = self.db['weather_anomalies']
            weather_anomalies = await weather_collection.count_documents({
                'node_id': node_id,
                'ts': {'$gte': datetime.utcnow() - timedelta(days=7)}
            })
            
            # Get extracted events
            events_collection = self.db['extracted_events']
            extracted_events = await events_collection.count_documents({
                'node_id': node_id,
                'ts_event': {'$gte': datetime.utcnow() - timedelta(days=7)}
            })
            
            return {
                'node_id': node_id,
                'recent_news_count': recent_news,
                'negative_sentiment_count': negative_news,
                'weather_anomalies_count': weather_anomalies,
                'extracted_events_count': extracted_events,
                'risk_score': self._calculate_risk_score(
                    recent_news, negative_news, weather_anomalies, extracted_events
                )
            }
            
        except Exception as e:
            logger.error(f"Error getting supplier risk summary for {node_id}: {e}")
            return {'error': str(e)}
    
    def _calculate_risk_score(self, news_count: int, negative_news: int, 
                            weather_anomalies: int, extracted_events: int) -> float:
        """Calculate a simple risk score."""
        # Simple weighted scoring
        score = (
            news_count * 0.1 +
            negative_news * 0.3 +
            weather_anomalies * 0.2 +
            extracted_events * 0.4
        )
        return min(100, max(0, score))
    
    async def get_global_risk_metrics(self) -> Dict[str, Any]:
        """Get global risk metrics across all suppliers."""
        try:
            # Get total counts
            nodes_count = await self.db['nodes'].count_documents({})
            
            # Get recent activity
            recent_cutoff = datetime.utcnow() - timedelta(days=7)
            
            recent_news = await self.db['news_events'].count_documents({
                'ts': {'$gte': recent_cutoff}
            })
            
            negative_news = await self.db['news_events'].count_documents({
                'sentiment_score': {'$lt': -0.3},
                'ts': {'$gte': recent_cutoff}
            })
            
            weather_anomalies = await self.db['weather_anomalies'].count_documents({
                'ts': {'$gte': recent_cutoff}
            })
            
            extracted_events = await self.db['extracted_events'].count_documents({
                'ts_event': {'$gte': recent_cutoff}
            })
            
            return {
                'total_suppliers': nodes_count,
                'recent_news_events': recent_news,
                'negative_sentiment_events': negative_news,
                'weather_anomalies': weather_anomalies,
                'extracted_events': extracted_events,
                'negative_sentiment_rate': negative_news / recent_news if recent_news > 0 else 0,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting global risk metrics: {e}")
            return {'error': str(e)}