#!/usr/bin/env python3
"""
Seed the database with sample data for testing the frontend.
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
import random

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import db_manager
from core.db_models import get_models, NodeModel, NewsEventModel, WeatherAnomalyModel, MarketSignalModel
from core.models import Node, NewsEvent, SocialEvent, ExtractedEvent, WeatherAnomaly, MarketSignal, FeatureRow

async def seed_database():
    """Seed the database with sample data."""
    print("🌱 Seeding database with sample data...")
    
    try:
        # Connect to database
        await db_manager.connect_async()
        models = await get_models()
        
        # Create sample suppliers (nodes)
        suppliers = [
            {
                "name": "TechCorp Electronics",
                "country": "China",
                "lat": 31.2304,
                "lon": 121.4737,
                "node_type": "supplier",
                "tier": 1.0,
                "industry": "Electronics"
            },
            {
                "name": "Global Steel Works",
                "country": "Germany",
                "lat": 52.5200,
                "lon": 13.4050,
                "node_type": "supplier",
                "tier": 2.0,
                "industry": "Steel"
            },
            {
                "name": "Pacific Textiles",
                "country": "Bangladesh",
                "lat": 23.8103,
                "lon": 90.4125,
                "node_type": "supplier",
                "tier": 3.0,
                "industry": "Textiles"
            },
            {
                "name": "Lithium Solutions Inc",
                "country": "Australia",
                "lat": -33.8688,
                "lon": 151.2093,
                "node_type": "supplier",
                "tier": 1.0,
                "industry": "Batteries"
            },
            {
                "name": "Precision Components Ltd",
                "country": "Japan",
                "lat": 35.6762,
                "lon": 139.6503,
                "node_type": "supplier",
                "tier": 2.0,
                "industry": "Components"
            }
        ]
        
        print("📦 Creating sample suppliers...")
        node_model = NodeModel(models.nodes)
        for supplier_data in suppliers:
            node = Node.from_raw(**supplier_data)
            node_id = await node_model.create(node)
            print(f"✅ Created supplier: {supplier_data['name']}")
        
        # Create sample news events
        print("📰 Creating sample news events...")
        news_events = [
            {
                "node_id": "techcorp_electronics",
                "url": "https://example.com/news1",
                "headline": "TechCorp reports supply chain disruption",
                "snippet": "Major electronics supplier faces delays due to port congestion",
                "outlet": "Supply Chain News",
                "ts": datetime.utcnow() - timedelta(hours=2),
                "sentiment_score": -0.7,
                "language": "en"
            },
            {
                "node_id": "global_steel_works",
                "url": "https://example.com/news2",
                "headline": "Steel prices continue to rise",
                "snippet": "Global steel market shows strong demand and price increases",
                "outlet": "Metal Industry Weekly",
                "ts": datetime.utcnow() - timedelta(hours=5),
                "sentiment_score": 0.3,
                "language": "en"
            },
            {
                "node_id": "pacific_textiles",
                "url": "https://example.com/news3",
                "headline": "Textile factory expansion announced",
                "snippet": "Pacific Textiles plans to double production capacity",
                "outlet": "Manufacturing Today",
                "ts": datetime.utcnow() - timedelta(hours=8),
                "sentiment_score": 0.8,
                "language": "en"
            }
        ]
        
        news_model = NewsEventModel(models.news_events)
        for news_data in news_events:
            news = NewsEvent(**news_data)
            news_id = await news_model.create(news)
            print(f"✅ Created news event: {news_data['headline']}")
        
        # Create sample weather anomalies
        print("🌦️ Creating sample weather anomalies...")
        weather_anomalies = [
            {
                "node_id": "techcorp_electronics",
                "anomaly_type": "storm",
                "severity": "high",
                "value": 85.5,
                "threshold": 75.0,
                "ts": datetime.utcnow() - timedelta(hours=1),
                "duration_h": 6.0
            },
            {
                "node_id": "global_steel_works",
                "anomaly_type": "heavy_precip",
                "severity": "medium",
                "value": 45.2,
                "threshold": 30.0,
                "ts": datetime.utcnow() - timedelta(hours=3),
                "duration_h": 4.5
            }
        ]
        
        weather_model = WeatherAnomalyModel(models.weather_anomalies)
        for weather_data in weather_anomalies:
            weather = WeatherAnomaly(**weather_data)
            weather_id = await weather_model.create(weather)
            print(f"✅ Created weather anomaly: {weather_data['anomaly_type']} - {weather_data['severity']}")
        
        # Create sample market signals
        print("📈 Creating sample market signals...")
        market_signals = [
            {
                "node_id": "lithium_solutions_inc",
                "ticker": "LIT",
                "signal_type": "price_spike",
                "value": 125.50,
                "change_percentage": 15.2,
                "ts": datetime.utcnow() - timedelta(minutes=30)
            },
            {
                "node_id": "precision_components_ltd",
                "ticker": "PCL",
                "signal_type": "volume_surge",
                "value": 89.75,
                "change_percentage": 8.7,
                "ts": datetime.utcnow() - timedelta(minutes=45)
            }
        ]
        
        market_model = MarketSignalModel(models.market_signals)
        for market_data in market_signals:
            market = MarketSignal(**market_data)
            market_id = await market_model.create(market)
            print(f"✅ Created market signal: {market_data['ticker']}")
        
        print("\n🎉 Database seeding completed successfully!")
        print("📊 Summary:")
        print(f"  - Suppliers: {len(suppliers)}")
        print(f"  - News Events: {len(news_events)}")
        print(f"  - Weather Anomalies: {len(weather_anomalies)}")
        print(f"  - Market Signals: {len(market_signals)}")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        raise
    finally:
        await db_manager.disconnect_async()

if __name__ == "__main__":
    asyncio.run(seed_database())
