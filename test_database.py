"""
Test script for MongoDB database connection and functionality.
"""
import asyncio
import logging
from datetime import datetime
from core.database import db_manager, check_database_health
from core.db_models import get_models
from core.models import Node, NewsEvent
from core.db_utils import get_db_utils

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_database_connection():
    """Test basic database connection."""
    print("🔍 Testing database connection...")
    
    try:
        # Test connection
        health = await check_database_health()
        print(f"Database Health: {health['status']}")
        
        if health['status'] == 'healthy':
            print("✅ Database connection successful")
            return True
        else:
            print(f"❌ Database connection failed: {health.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False


async def test_database_operations():
    """Test basic database operations."""
    print("\n🧪 Testing database operations...")
    
    try:
        # Connect to database
        await db_manager.connect_async()
        models = await get_models()
        
        # Test creating a node
        test_node = Node.from_raw(
            name="Test Supplier",
            country="Test Country",
            lat=40.7128,
            lon=-74.0060,
            node_type="supplier",
            tier=1.0
        )
        
        print("Creating test node...")
        from core.db_models import NodeModel
        node_model = NodeModel(models.nodes)
        node_id = await node_model.create(test_node)
        print(f"✅ Node created with ID: {node_id}")
        
        # Test retrieving the node
        print("Retrieving test node...")
        retrieved_node = await node_model.get_by_id(test_node.node_id)
        if retrieved_node:
            print(f"✅ Node retrieved: {retrieved_node.name}")
        else:
            print("❌ Failed to retrieve node")
        
        # Test creating a news event
        test_news = NewsEvent(
            node_id=test_node.node_id,
            url="https://example.com/test-news",
            headline="Test News Headline",
            snippet="This is a test news snippet",
            outlet="Test News",
            ts=datetime.utcnow(),
            sentiment_score=0.5,
            language="en"
        )
        
        print("Creating test news event...")
        from core.db_models import NewsEventModel
        news_model = NewsEventModel(models.news_events)
        news_id = await news_model.create(test_news)
        print(f"✅ News event created with ID: {news_id}")
        
        # Test retrieving news events
        print("Retrieving news events...")
        news_events = await news_model.get_by_node_id(test_node.node_id)
        print(f"✅ Retrieved {len(news_events)} news events")
        
        # Test database statistics
        print("Getting database statistics...")
        db_utils = await get_db_utils()
        stats = await db_utils.get_database_stats()
        print("✅ Database statistics:")
        for collection, data in stats.items():
            if isinstance(data, dict) and 'total_documents' in data:
                print(f"  {collection}: {data['total_documents']} documents")
        
        # Clean up test data
        print("Cleaning up test data...")
        await node_model.delete(test_node.node_id)
        await news_model.schema.delete_one({"node_id": test_node.node_id})
        print("✅ Test data cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Database operations test failed: {e}")
        return False
    finally:
        await db_manager.disconnect_async()


async def test_database_indexes():
    """Test database indexes."""
    print("\n📊 Testing database indexes...")
    
    try:
        await db_manager.connect_async()
        models = await get_models()
        
        # Initialize indexes
        await models.initialize_indexes()
        print("✅ Database indexes initialized")
        
        # Test index creation (this will not fail if indexes already exist)
        print("✅ Index creation test completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Database indexes test failed: {e}")
        return False
    finally:
        await db_manager.disconnect_async()


async def main():
    """Run all database tests."""
    print("🚀 Starting CERONIX Database Tests")
    print("=" * 50)
    
    # Test 1: Connection
    connection_ok = await test_database_connection()
    
    if not connection_ok:
        print("\n❌ Database connection failed. Please check your MongoDB setup.")
        return
    
    # Test 2: Indexes
    indexes_ok = await test_database_indexes()
    
    # Test 3: Operations
    operations_ok = await test_database_operations()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    print(f"Connection: {'✅ PASS' if connection_ok else '❌ FAIL'}")
    print(f"Indexes: {'✅ PASS' if indexes_ok else '❌ FAIL'}")
    print(f"Operations: {'✅ PASS' if operations_ok else '❌ FAIL'}")
    
    if all([connection_ok, indexes_ok, operations_ok]):
        print("\n🎉 All database tests passed! Your MongoDB integration is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the error messages above.")


if __name__ == "__main__":
    asyncio.run(main())
