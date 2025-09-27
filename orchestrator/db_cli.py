"""
Database CLI commands for CERONIX supply chain risk analysis system.
"""
import asyncio
import typer
from typing import Optional, List
from datetime import datetime, timedelta
import logging

from core.database import db_manager, check_database_health
from core.db_models import get_models
from core.db_utils import get_db_utils, get_migration_utils
from core.init_database import initialize_database, seed_initial_data, reset_database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = typer.Typer(help="CERONIX Database Management CLI")


@app.command()
def health():
    """Check database health and connection status."""
    async def _health_check():
        try:
            health_status = await check_database_health()
            typer.echo(f"Database Health: {health_status['status']}")
            if health_status['status'] == 'healthy':
                typer.echo(f"Database: {health_status['database']}")
                typer.echo("✅ Database is healthy and connected")
            else:
                typer.echo(f"❌ Database error: {health_status.get('error', 'Unknown error')}")
        except Exception as e:
            typer.echo(f"❌ Failed to check database health: {e}")
    
    asyncio.run(_health_check())


@app.command()
def init():
    """Initialize database with indexes and basic setup."""
    async def _init():
        try:
            typer.echo("🚀 Initializing database...")
            result = await initialize_database()
            
            if result['status'] == 'success':
                typer.echo("✅ Database initialized successfully")
                typer.echo(f"Health: {result['health']['status']}")
            else:
                typer.echo(f"❌ Database initialization failed: {result.get('error', 'Unknown error')}")
        except Exception as e:
            typer.echo(f"❌ Failed to initialize database: {e}")
    
    asyncio.run(_init())


@app.command()
def seed():
    """Seed database with initial data from CSV and YAML files."""
    async def _seed():
        try:
            typer.echo("🌱 Seeding database with initial data...")
            result = await seed_initial_data()
            
            if result['status'] == 'success':
                typer.echo("✅ Database seeded successfully")
            else:
                typer.echo(f"❌ Database seeding failed: {result.get('error', 'Unknown error')}")
        except Exception as e:
            typer.echo(f"❌ Failed to seed database: {e}")
    
    asyncio.run(_seed())


@app.command()
def reset():
    """Reset database (WARNING: This will delete all data)."""
    confirm = typer.confirm("⚠️  This will delete ALL data in the database. Are you sure?")
    if not confirm:
        typer.echo("Operation cancelled.")
        return
    
    async def _reset():
        try:
            typer.echo("🔄 Resetting database...")
            result = await reset_database()
            
            if result['status'] == 'success':
                typer.echo("✅ Database reset successfully")
                typer.echo(f"Dropped collections: {', '.join(result['dropped_collections'])}")
            else:
                typer.echo(f"❌ Database reset failed: {result.get('error', 'Unknown error')}")
        except Exception as e:
            typer.echo(f"❌ Failed to reset database: {e}")
    
    asyncio.run(_reset())


@app.command()
def stats():
    """Show database statistics and collection counts."""
    async def _stats():
        try:
            await db_manager.connect_async()
            db_utils = await get_db_utils()
            stats = await db_utils.get_database_stats()
            
            typer.echo("📊 Database Statistics:")
            typer.echo("=" * 50)
            
            for collection, data in stats.items():
                if isinstance(data, dict) and 'total_documents' in data:
                    typer.echo(f"{collection}:")
                    typer.echo(f"  Total documents: {data['total_documents']}")
                    typer.echo(f"  Recent (24h): {data['recent_documents_24h']}")
                else:
                    typer.echo(f"{collection}: {data}")
            
        except Exception as e:
            typer.echo(f"❌ Failed to get database stats: {e}")
        finally:
            await db_manager.disconnect_async()
    
    asyncio.run(_stats())


@app.command()
def cleanup(
    days: int = typer.Option(30, help="Number of days to keep data")
):
    """Clean up old data beyond specified days."""
    async def _cleanup():
        try:
            await db_manager.connect_async()
            db_utils = await get_db_utils()
            
            typer.echo(f"🧹 Cleaning up data older than {days} days...")
            result = await db_utils.cleanup_old_data(days)
            
            if 'error' not in result:
                typer.echo("✅ Cleanup completed:")
                for collection, count in result.items():
                    typer.echo(f"  {collection}: {count} documents deleted")
            else:
                typer.echo(f"❌ Cleanup failed: {result['error']}")
                
        except Exception as e:
            typer.echo(f"❌ Failed to cleanup database: {e}")
        finally:
            await db_manager.disconnect_async()
    
    asyncio.run(_cleanup())


@app.command()
def backup(
    collection: Optional[str] = typer.Option(None, help="Specific collection to backup (default: all)")
):
    """Create backup of database collections."""
    async def _backup():
        try:
            await db_manager.connect_async()
            db_utils = await get_db_utils()
            
            if collection:
                typer.echo(f"💾 Creating backup of {collection}...")
                result = await db_utils.backup_collection(collection)
                
                if result['status'] == 'success':
                    typer.echo(f"✅ Backup created successfully")
                    typer.echo(f"Backup ID: {result['backup_id']}")
                    typer.echo(f"Documents: {result['document_count']}")
                else:
                    typer.echo(f"❌ Backup failed: {result['error']}")
            else:
                # Backup all collections
                collections = [
                    'nodes', 'news_events', 'social_events', 'extracted_events',
                    'weather_anomalies', 'market_signals', 'feature_rows', 'region_configs'
                ]
                
                typer.echo("💾 Creating backup of all collections...")
                for coll in collections:
                    result = await db_utils.backup_collection(coll)
                    if result['status'] == 'success':
                        typer.echo(f"✅ {coll}: {result['document_count']} documents backed up")
                    else:
                        typer.echo(f"❌ {coll}: {result['error']}")
                        
        except Exception as e:
            typer.echo(f"❌ Failed to backup database: {e}")
        finally:
            await db_manager.disconnect_async()
    
    asyncio.run(_backup())


@app.command()
def migrate_csv(
    csv_file: str = typer.Argument(..., help="Path to CSV file"),
    collection: str = typer.Argument(..., help="Target collection name")
):
    """Migrate CSV data to MongoDB collection."""
    async def _migrate():
        try:
            await db_manager.connect_async()
            migration_utils = await get_migration_utils()
            
            typer.echo(f"📥 Migrating {csv_file} to {collection}...")
            result = await migration_utils.migrate_csv_to_mongodb(csv_file, collection)
            
            if result['status'] == 'success':
                typer.echo(f"✅ Migration completed successfully")
                typer.echo(f"Migrated documents: {result['migrated_documents']}")
            else:
                typer.echo(f"❌ Migration failed: {result['error']}")
                
        except Exception as e:
            typer.echo(f"❌ Failed to migrate CSV: {e}")
        finally:
            await db_manager.disconnect_async()
    
    asyncio.run(_migrate())


@app.command()
def export_csv(
    collection: str = typer.Argument(..., help="Collection name to export"),
    output_file: str = typer.Argument(..., help="Output CSV file path")
):
    """Export MongoDB collection to CSV file."""
    async def _export():
        try:
            await db_manager.connect_async()
            migration_utils = await get_migration_utils()
            
            typer.echo(f"📤 Exporting {collection} to {output_file}...")
            result = await migration_utils.export_collection_to_csv(collection, output_file)
            
            if result['status'] == 'success':
                typer.echo(f"✅ Export completed successfully")
                typer.echo(f"Exported documents: {result['exported_documents']}")
            else:
                typer.echo(f"❌ Export failed: {result['error']}")
                
        except Exception as e:
            typer.echo(f"❌ Failed to export collection: {e}")
        finally:
            await db_manager.disconnect_async()
    
    asyncio.run(_export())


@app.command()
def collections():
    """List all database collections and their document counts."""
    async def _collections():
        try:
            await db_manager.connect_async()
            models = await get_models()
            
            typer.echo("📋 Database Collections:")
            typer.echo("=" * 50)
            
            collections = [
                'nodes', 'news_events', 'social_events', 'extracted_events',
                'weather_anomalies', 'market_signals', 'feature_rows', 'region_configs'
            ]
            
            for collection_name in collections:
                try:
                    count = await models.db[collection_name].count_documents({})
                    typer.echo(f"{collection_name}: {count} documents")
                except Exception as e:
                    typer.echo(f"{collection_name}: Error - {e}")
                    
        except Exception as e:
            typer.echo(f"❌ Failed to list collections: {e}")
        finally:
            await db_manager.disconnect_async()
    
    asyncio.run(_collections())


if __name__ == "__main__":
    app()
