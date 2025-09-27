"""
Database initialization script.
"""
import asyncio
import logging
from typing import Dict, Any
from .database import db_manager, check_database_health
from .db_models import get_models
from .db_utils import get_db_utils
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def initialize_database() -> Dict[str, Any]:
    """Initialize the database with indexes and basic setup."""
    try:
        logger.info("Starting database initialization...")
        
        # Connect to database
        await db_manager.connect_async()
        logger.info("Connected to MongoDB")
        
        # Get models and initialize indexes
        models = await get_models()
        await models.initialize_indexes()
        logger.info("Database indexes created successfully")
        
        # Perform health check
        health = await check_database_health()
        logger.info(f"Database health check: {health['status']}")
        
        # Get initial stats
        db_utils = await get_db_utils()
        stats = await db_utils.get_database_stats()
        logger.info(f"Database stats: {stats}")
        
        return {
            "status": "success",
            "health": health,
            "stats": stats,
            "message": "Database initialized successfully"
        }
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Database initialization failed"
        }
    finally:
        await db_manager.disconnect_async()


async def seed_initial_data() -> Dict[str, Any]:
    """Seed the database with initial data."""
    try:
        logger.info("Seeding initial data...")
        
        # Connect to database
        await db_manager.connect_async()
        models = await get_models()
        
        # Seed region configurations from YAML
        from .io import load_yaml
        yaml_path = "data/inputs/allowlist_regions.yaml"
        
        if os.path.exists(yaml_path):
            allowlist_data = load_yaml(yaml_path)
            if allowlist_data and "regions" in allowlist_data:
                for region_name, region_data in allowlist_data["regions"].items():
                    from .models import RegionConfig
                    region_config = RegionConfig(name=region_name, outlets=region_data.get("outlets", []))
                    await models.region_configs.create(region_config)
                logger.info(f"Seeded {len(allowlist_data['regions'])} region configurations")
        
        # Seed suppliers from CSV
        csv_path = "data/inputs/suppliers_seed.csv"
        if os.path.exists(csv_path):
            import pandas as pd
            from .models import Node
            
            df = pd.read_csv(csv_path)
            nodes_created = 0
            
            for _, row in df.iterrows():
                try:
                    node = Node.from_raw(
                        name=row.get("name", ""),
                        country=row.get("country", ""),
                        lat=float(row.get("lat", 0)),
                        lon=float(row.get("lon", 0)),
                        node_type=row.get("node_type", "supplier"),
                        tier=float(row.get("tier", 1.0)),
                        category=row.get("category"),
                        region=row.get("region")
                    )
                    await models.nodes.create(node)
                    nodes_created += 1
                except Exception as e:
                    logger.warning(f"Failed to create node from row {row.get('name', 'unknown')}: {e}")
            
            logger.info(f"Seeded {nodes_created} supplier nodes")
        
        return {
            "status": "success",
            "message": "Initial data seeded successfully"
        }
        
    except Exception as e:
        logger.error(f"Data seeding failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Data seeding failed"
        }
    finally:
        await db_manager.disconnect_async()


async def reset_database() -> Dict[str, Any]:
    """Reset the database (WARNING: This will delete all data)."""
    try:
        logger.warning("Resetting database - ALL DATA WILL BE LOST!")
        
        # Connect to database
        await db_manager.connect_async()
        models = await get_models()
        
        # Drop all collections
        collections = [
            'nodes', 'news_events', 'social_events', 'extracted_events',
            'weather_anomalies', 'market_signals', 'feature_rows', 'region_configs'
        ]
        
        dropped_collections = []
        for collection_name in collections:
            try:
                await models.db[collection_name].drop()
                dropped_collections.append(collection_name)
                logger.info(f"Dropped collection: {collection_name}")
            except Exception as e:
                logger.warning(f"Failed to drop collection {collection_name}: {e}")
        
        # Reinitialize indexes
        await models.initialize_indexes()
        logger.info("Recreated database indexes")
        
        return {
            "status": "success",
            "dropped_collections": dropped_collections,
            "message": "Database reset successfully"
        }
        
    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Database reset failed"
        }
    finally:
        await db_manager.disconnect_async()


async def main():
    """Main function for database initialization."""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "init":
            result = await initialize_database()
        elif command == "seed":
            result = await seed_initial_data()
        elif command == "reset":
            result = await reset_database()
        elif command == "health":
            await db_manager.connect_async()
            result = await check_database_health()
            await db_manager.disconnect_async()
        else:
            result = {"status": "error", "message": f"Unknown command: {command}"}
    else:
        # Default: initialize database
        result = await initialize_database()
    
    print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
