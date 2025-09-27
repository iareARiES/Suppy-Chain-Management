"""
Database connection for API layer
"""
from core.database import get_database as get_core_database
from motor.motor_asyncio import AsyncIOMotorDatabase

async def get_database() -> AsyncIOMotorDatabase:
    """Get database instance for API layer."""
    return await get_core_database()
