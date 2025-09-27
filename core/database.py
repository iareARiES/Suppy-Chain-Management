"""
Database configuration and connection management for MongoDB with Mongoose-like functionality.
"""
import os
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration settings."""
    
    def __init__(self):
        self.host = os.getenv('MONGODB_HOST', 'localhost')
        self.port = int(os.getenv('MONGODB_PORT', '27017'))
        self.database_name = os.getenv('MONGODB_DATABASE', 'Ceronix')
        self.username = os.getenv('MONGODB_USERNAME')
        self.password = os.getenv('MONGODB_PASSWORD')
        self.auth_source = os.getenv('MONGODB_AUTH_SOURCE', 'admin')
        self.connection_timeout = int(os.getenv('MONGODB_CONNECTION_TIMEOUT', '5000'))
        self.server_selection_timeout = int(os.getenv('MONGODB_SERVER_SELECTION_TIMEOUT', '5000'))
        
    @property
    def connection_string(self) -> str:
        """Generate MongoDB connection string."""
        if self.username and self.password:
            return f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/{self.database_name}?authSource={self.auth_source}"
        else:
            return f"mongodb://{self.host}:{self.port}/{self.database_name}"


class DatabaseManager:
    """MongoDB database manager with async and sync support."""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self._async_client: Optional[AsyncIOMotorClient] = None
        self._sync_client: Optional[MongoClient] = None
        self._database: Optional[AsyncIOMotorDatabase] = None
        
    async def connect_async(self) -> AsyncIOMotorDatabase:
        """Establish async connection to MongoDB."""
        try:
            if not self._async_client:
                self._async_client = AsyncIOMotorClient(
                    self.config.connection_string,
                    serverSelectionTimeoutMS=self.config.server_selection_timeout,
                    connectTimeoutMS=self.config.connection_timeout
                )
                
            # Test connection
            await self._async_client.admin.command('ping')
            self._database = self._async_client[self.config.database_name]
            
            logger.info(f"Successfully connected to MongoDB database: {self.config.database_name}")
            return self._database
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
            
    def connect_sync(self) -> 'Database':
        """Establish sync connection to MongoDB."""
        try:
            if not self._sync_client:
                self._sync_client = MongoClient(
                    self.config.connection_string,
                    serverSelectionTimeoutMS=self.config.server_selection_timeout,
                    connectTimeoutMS=self.config.connection_timeout
                )
                
            # Test connection
            self._sync_client.admin.command('ping')
            database = self._sync_client[self.config.database_name]
            
            logger.info(f"Successfully connected to MongoDB database: {self.config.database_name}")
            return database
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
            
    async def disconnect_async(self):
        """Close async connection."""
        if self._async_client:
            self._async_client.close()
            self._async_client = None
            self._database = None
            logger.info("Async MongoDB connection closed")
            
    def disconnect_sync(self):
        """Close sync connection."""
        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None
            logger.info("Sync MongoDB connection closed")
            
    @property
    def database(self) -> Optional[AsyncIOMotorDatabase]:
        """Get the current database instance."""
        return self._database
        
    @asynccontextmanager
    async def get_database(self):
        """Context manager for database operations."""
        try:
            db = await self.connect_async()
            yield db
        finally:
            await self.disconnect_async()


# Global database manager instance
db_manager = DatabaseManager()


async def get_database() -> AsyncIOMotorDatabase:
    """Get database instance for dependency injection."""
    if db_manager.database is None:
        await db_manager.connect_async()
    return db_manager.database


def get_sync_database():
    """Get sync database instance."""
    return db_manager.connect_sync()


# Database health check
async def check_database_health() -> Dict[str, Any]:
    """Check database connection health."""
    try:
        db = await get_database()
        result = await db.command("ping")
        return {
            "status": "healthy",
            "database": db_manager.config.database_name,
            "ping": result
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "database": db_manager.config.database_name
        }
