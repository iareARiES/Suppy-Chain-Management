#!/usr/bin/env python3
"""
System test script for CERONIX Supply Chain Risk Analysis
This script tests the complete system functionality.
"""
import os
import sys
import asyncio
import logging
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test all imports."""
    logger.info("Testing imports...")
    
    try:
        # Test core imports
        from core.database import get_database
        from core.models import Node, NewsEvent, WeatherAnomaly
        from core.schemas import NodeSchema, NewsEventSchema
        from core.db_utils import DatabaseUtils
        from core.rate import api_rate_limiter
        logger.info("✓ Core modules imported successfully")
        
        # Test agent imports
        from agents.agent0_registry import RegistryAgent
        from agents.agent1_social import SocialAgent
        from agents.agent2_news import NewsAgent
        from agents.agent4_crawl import CrawlAgent
        from agents.agent5_weather import WeatherAgent
        from agents.agent6_features import FeatureAgent
        from agents.agent7_export import ExportAgent
        logger.info("✓ All agents imported successfully")
        
        # Test API imports
        from api.main import app
        from api.services import SupplierService, RiskAnalysisService
        from api.models import SupplierResponse, RiskFactorResponse
        logger.info("✓ API modules imported successfully")
        
        return True
        
    except ImportError as e:
        logger.error(f"✗ Import failed: {e}")
        return False

def test_database_connection():
    """Test database connection."""
    logger.info("Testing database connection...")
    
    try:
        from core.database import check_database_health
        import asyncio
        
        async def test_db():
            health = await check_database_health()
            return health
        
        health = asyncio.run(test_db())
        
        if health.get("status") == "healthy":
            logger.info("✓ Database connection successful")
            return True
        else:
            logger.warning(f"⚠ Database connection issue: {health}")
            return False
            
    except Exception as e:
        logger.warning(f"⚠ Database connection failed: {e}")
        return False

def test_agents():
    """Test individual agents."""
    logger.info("Testing agents...")
    
    try:
        # Test registry agent
        from agents.agent0_registry import RegistryAgent
        registry_agent = RegistryAgent()
        logger.info("✓ Registry agent initialized")
        
        # Test news agent
        from agents.agent2_news import NewsAgent
        news_agent = NewsAgent()
        logger.info("✓ News agent initialized")
        
        # Test weather agent
        from agents.agent5_weather import WeatherAgent
        weather_agent = WeatherAgent()
        logger.info("✓ Weather agent initialized")
        
        # Test feature agent
        from agents.agent6_features import FeatureAgent
        feature_agent = FeatureAgent()
        logger.info("✓ Feature agent initialized")
        
        # Test export agent
        from agents.agent7_export import ExportAgent
        export_agent = ExportAgent()
        logger.info("✓ Export agent initialized")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Agent test failed: {e}")
        return False

def test_api_services():
    """Test API services."""
    logger.info("Testing API services...")
    
    try:
        from api.services import SupplierService, RiskAnalysisService, RouteService, AlertService, MetricService
        
        # Test service initialization
        supplier_service = SupplierService()
        risk_service = RiskAnalysisService()
        route_service = RouteService()
        alert_service = AlertService()
        metric_service = MetricService()
        
        logger.info("✓ All API services initialized")
        return True
        
    except Exception as e:
        logger.error(f"✗ API service test failed: {e}")
        return False

def test_data_files():
    """Test data files."""
    logger.info("Testing data files...")
    
    # Check required input files
    required_files = [
        "data/inputs/suppliers_seed.csv",
        "data/inputs/allowlist_regions.yaml",
        "config/settings.yaml"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        logger.warning(f"⚠ Missing files: {missing_files}")
        return False
    else:
        logger.info("✓ All required data files found")
        return True

def test_pipeline_execution():
    """Test pipeline execution."""
    logger.info("Testing pipeline execution...")
    
    try:
        # Test registry agent execution
        from agents.agent0_registry import RegistryAgent
        from core.io import read_yaml
        
        # Load allowlist
        allowlist = read_yaml("data/inputs/allowlist_regions.yaml")
        
        # Run registry agent
        registry_agent = RegistryAgent()
        nodes = registry_agent.run()
        
        if nodes and len(nodes) > 0:
            logger.info(f"✓ Registry agent executed successfully: {len(nodes)} nodes created")
        else:
            logger.warning("⚠ Registry agent returned no nodes")
            return False
        
        # Test feature agent with mock data
        from agents.agent6_features import FeatureAgent
        feature_agent = FeatureAgent()
        features_df = feature_agent.run(nodes)
        
        if not features_df.empty:
            logger.info(f"✓ Feature agent executed successfully: {len(features_df)} feature rows")
        else:
            logger.warning("⚠ Feature agent returned no features")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Pipeline execution test failed: {e}")
        return False

def test_frontend_files():
    """Test frontend files."""
    logger.info("Testing frontend files...")
    
    required_files = [
        "frontend/package.json",
        "frontend/src/App.js",
        "frontend/src/hooks/useApiData.js",
        "frontend/src/services/api.js"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        logger.warning(f"⚠ Missing frontend files: {missing_files}")
        return False
    else:
        logger.info("✓ All required frontend files found")
        return True

def test_configuration():
    """Test configuration files."""
    logger.info("Testing configuration...")
    
    try:
        # Test settings.yaml
        from core.io import read_yaml
        settings = read_yaml("config/settings.yaml")
        
        if settings:
            logger.info("✓ Settings configuration loaded")
        else:
            logger.warning("⚠ Settings configuration is empty")
            return False
        
        # Test MongoDB config
        mongodb_config = read_yaml("config/mongodb.yaml")
        
        if mongodb_config:
            logger.info("✓ MongoDB configuration loaded")
        else:
            logger.warning("⚠ MongoDB configuration is empty")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Configuration test failed: {e}")
        return False

def test_environment():
    """Test environment variables."""
    logger.info("Testing environment...")
    
    # Check if .env file exists
    if not Path(".env").exists():
        logger.warning("⚠ .env file not found")
        return False
    
    # Check required environment variables
    required_vars = [
        "MONGODB_HOST",
        "MONGODB_PORT", 
        "MONGODB_DATABASE"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"⚠ Missing environment variables: {missing_vars}")
        return False
    else:
        logger.info("✓ Environment variables configured")
        return True

def run_comprehensive_test():
    """Run comprehensive system test."""
    logger.info("🧪 Starting Comprehensive System Test")
    logger.info("=" * 70)
    
    tests = [
        ("Import Test", test_imports),
        ("Database Connection", test_database_connection),
        ("Agent Test", test_agents),
        ("API Services Test", test_api_services),
        ("Data Files Test", test_data_files),
        ("Pipeline Execution Test", test_pipeline_execution),
        ("Frontend Files Test", test_frontend_files),
        ("Configuration Test", test_configuration),
        ("Environment Test", test_environment),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            logger.error(f"✗ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("=" * 70)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! System is ready to use.")
        return True
    else:
        logger.warning(f"⚠ {total - passed} tests failed. Please check the issues above.")
        return False

def main():
    """Main test function."""
    success = run_comprehensive_test()
    
    if success:
        logger.info("\n🚀 System is ready!")
        logger.info("You can now:")
        logger.info("1. Start MongoDB: docker-compose up mongodb -d")
        logger.info("2. Run the pipeline: python run_complete_pipeline.py")
        logger.info("3. Start the API: python -m uvicorn api.main:app --reload")
        logger.info("4. Start the frontend: cd frontend && npm start")
    else:
        logger.error("\n❌ System has issues that need to be resolved.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
