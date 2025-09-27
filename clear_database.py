#!/usr/bin/env python3
"""
Clear the database collections.
"""
import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import db_manager

async def clear_database():
    """Clear all collections."""
    print("🧹 Clearing database collections...")
    
    try:
        await db_manager.connect_async()
        
        # Clear collections
        collections = ['news_events', 'nodes', 'weather_anomalies', 'market_signals', 'social_events', 'extracted_events', 'feature_rows']
        
        for collection_name in collections:
            try:
                await db_manager.database[collection_name].drop()
                print(f"✅ Cleared {collection_name}")
            except Exception as e:
                print(f"⚠️ Could not clear {collection_name}: {e}")
        
        print("🎉 Database cleared successfully!")
        
    except Exception as e:
        print(f"❌ Error clearing database: {e}")
        raise
    finally:
        await db_manager.disconnect_async()

if __name__ == "__main__":
    asyncio.run(clear_database())

