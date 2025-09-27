#!/usr/bin/env python3
"""
System setup script for CERONIX Supply Chain Risk Analysis
This script sets up the complete system environment.
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_command(command, description, check=True):
    """Run a command and log the result."""
    logger.info(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        if result.stdout:
            logger.info(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed: {e}")
        if e.stderr:
            logger.error(f"Error: {e.stderr}")
        return False

def create_directories():
    """Create necessary directories."""
    logger.info("Creating directories...")
    
    directories = [
        "data/inputs",
        "data/outputs", 
        "cache",
        "logs",
        "frontend/build",
        "frontend/public"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {directory}")

def setup_environment():
    """Setup environment file."""
    logger.info("Setting up environment...")
    
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        logger.info("Created .env file from template")
        logger.warning("Please edit .env file with your actual API keys")
    elif env_file.exists():
        logger.info(".env file already exists")
    else:
        logger.warning("No env.example file found")

def install_python_dependencies():
    """Install Python dependencies."""
    logger.info("Installing Python dependencies...")
    
    if not Path("requirements.txt").exists():
        logger.error("requirements.txt not found")
        return False
    
    return run_command("pip install -r requirements.txt", "Installing Python packages")

def install_frontend_dependencies():
    """Install frontend dependencies."""
    logger.info("Installing frontend dependencies...")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        logger.error("Frontend directory not found")
        return False
    
    # Check if package.json exists
    if not (frontend_dir / "package.json").exists():
        logger.error("package.json not found in frontend directory")
        return False
    
    # Install npm dependencies
    return run_command("cd frontend && npm install", "Installing npm packages")

def check_dependencies():
    """Check if required dependencies are installed."""
    logger.info("Checking dependencies...")
    
    # Check Python
    python_version = subprocess.run([sys.executable, "--version"], capture_output=True, text=True)
    if python_version.returncode == 0:
        logger.info(f"Python: {python_version.stdout.strip()}")
    else:
        logger.error("Python not found")
        return False
    
    # Check Node.js
    node_version = subprocess.run(["node", "--version"], capture_output=True, text=True)
    if node_version.returncode == 0:
        logger.info(f"Node.js: {node_version.stdout.strip()}")
    else:
        logger.error("Node.js not found")
        return False
    
    # Check npm
    npm_version = subprocess.run(["npm", "--version"], capture_output=True, text=True)
    if npm_version.returncode == 0:
        logger.info(f"npm: {npm_version.stdout.strip()}")
    else:
        logger.error("npm not found")
        return False
    
    return True

def test_imports():
    """Test if all required modules can be imported."""
    logger.info("Testing imports...")
    
    required_modules = [
        "fastapi",
        "uvicorn", 
        "motor",
        "pymongo",
        "pandas",
        "numpy",
        "requests",
        "prefect",
        "typer"
    ]
    
    failed_imports = []
    
    for module in required_modules:
        try:
            __import__(module)
            logger.info(f"✓ {module}")
        except ImportError as e:
            logger.error(f"✗ {module}: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        logger.error(f"Failed to import: {failed_imports}")
        return False
    
    return True

def test_agents():
    """Test if agents can be imported."""
    logger.info("Testing agent imports...")
    
    agents = [
        "agents.agent0_registry",
        "agents.agent1_social", 
        "agents.agent2_news",
        "agents.agent4_crawl",
        "agents.agent5_weather",
        "agents.agent6_features",
        "agents.agent7_export"
    ]
    
    failed_agents = []
    
    for agent in agents:
        try:
            __import__(agent)
            logger.info(f"✓ {agent}")
        except ImportError as e:
            logger.error(f"✗ {agent}: {e}")
            failed_agents.append(agent)
    
    if failed_agents:
        logger.error(f"Failed to import agents: {failed_agents}")
        return False
    
    return True

def test_core_modules():
    """Test if core modules can be imported."""
    logger.info("Testing core module imports...")
    
    core_modules = [
        "core.database",
        "core.models",
        "core.schemas",
        "core.db_utils",
        "core.rate",
        "core.io",
        "core.utils"
    ]
    
    failed_modules = []
    
    for module in core_modules:
        try:
            __import__(module)
            logger.info(f"✓ {module}")
        except ImportError as e:
            logger.error(f"✗ {module}: {e}")
            failed_modules.append(module)
    
    if failed_modules:
        logger.error(f"Failed to import core modules: {failed_modules}")
        return False
    
    return True

def create_sample_data():
    """Create sample data files if they don't exist."""
    logger.info("Creating sample data...")
    
    # Create sample suppliers CSV
    suppliers_file = Path("data/inputs/suppliers_seed.csv")
    if not suppliers_file.exists():
        sample_suppliers = """name,country,city,category,site_url,ticker
TechCorp Semiconductors,Taiwan,Taipei,semiconductors,https://techcorp.com,TCORP
Global Steel Works,China,Shanghai,steel,https://globalsteel.com,GSW
EuroElectronics,Germany,Berlin,electronics,https://euroelectronics.com,EURO
"""
        suppliers_file.parent.mkdir(parents=True, exist_ok=True)
        suppliers_file.write_text(sample_suppliers)
        logger.info("Created sample suppliers CSV")
    
    # Create sample allowlist YAML
    allowlist_file = Path("data/inputs/allowlist_regions.yaml")
    if not allowlist_file.exists():
        sample_allowlist = """regions:
  taiwan:
    name: "Taiwan"
    outlets:
      - name: "Taiwan News"
        url: "https://www.taiwannews.com.tw/en/rss"
        type: "rss"
  china:
    name: "China"
    outlets:
      - name: "China Daily"
        url: "https://www.chinadaily.com.cn/rss"
        type: "rss"
  germany:
    name: "Germany"
    outlets:
      - name: "Deutsche Welle"
        url: "https://rss.dw.com/rdf/rss-en-all"
        type: "rss"
"""
        allowlist_file.parent.mkdir(parents=True, exist_ok=True)
        allowlist_file.write_text(sample_allowlist)
        logger.info("Created sample allowlist YAML")

def main():
    """Main setup function."""
    logger.info("🚀 Starting CERONIX Supply Chain Risk Analysis System Setup")
    logger.info("=" * 70)
    
    # Check dependencies
    if not check_dependencies():
        logger.error("❌ Dependency check failed")
        return False
    
    # Create directories
    create_directories()
    
    # Setup environment
    setup_environment()
    
    # Install Python dependencies
    if not install_python_dependencies():
        logger.error("❌ Failed to install Python dependencies")
        return False
    
    # Install frontend dependencies
    if not install_frontend_dependencies():
        logger.error("❌ Failed to install frontend dependencies")
        return False
    
    # Test imports
    if not test_imports():
        logger.error("❌ Import test failed")
        return False
    
    # Test core modules
    if not test_core_modules():
        logger.error("❌ Core module test failed")
        return False
    
    # Test agents
    if not test_agents():
        logger.error("❌ Agent test failed")
        return False
    
    # Create sample data
    create_sample_data()
    
    logger.info("✅ System setup completed successfully!")
    logger.info("=" * 70)
    logger.info("Next steps:")
    logger.info("1. Edit .env file with your actual API keys")
    logger.info("2. Start MongoDB: docker-compose up mongodb -d")
    logger.info("3. Run the pipeline: python run_complete_pipeline.py")
    logger.info("4. Start the API: python -m uvicorn api.main:app --reload")
    logger.info("5. Start the frontend: cd frontend && npm start")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
