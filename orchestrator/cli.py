"""
Command-line interface for the supply chain risk analysis system.
"""
import logging
import sys
from pathlib import Path
from typing import Optional

import typer
from prefect import serve
from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule

from flow_daily import daily_supply_chain_flow, registry_only_flow, export_only_flow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/supply_agents.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

app = typer.Typer(help="Supply Chain Risk Analysis CLI")


@app.command()
def run_all(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging")
):
    """Run the complete supply chain risk analysis pipeline."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    typer.echo("🚀 Starting complete supply chain risk analysis pipeline...")
    
    try:
        result = daily_supply_chain_flow()
        
        typer.echo("✅ Pipeline completed successfully!")
        typer.echo(f"📊 Results:")
        typer.echo(f"   - Nodes processed: {result['nodes_count']}")
        typer.echo(f"   - Social events: {result['social_events']}")
        typer.echo(f"   - News articles: {result['news_articles']}")
        typer.echo(f"   - Extracted events: {result['extracted_events']}")
        typer.echo(f"   - Weather anomalies: {result['weather_anomalies']}")
        typer.echo(f"   - Feature rows: {result['feature_rows']}")
        typer.echo(f"   - Output file: {result['output_path']}")
        
    except Exception as e:
        typer.echo(f"❌ Pipeline failed: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def export_csv(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging")
):
    """Export features CSV (assumes data collection already completed)."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    typer.echo("📤 Exporting features CSV...")
    
    try:
        result = export_only_flow()
        
        typer.echo("✅ CSV export completed successfully!")
        typer.echo(f"📁 Output file: {result['output_path']}")
        
    except Exception as e:
        typer.echo(f"❌ CSV export failed: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def regen_registry(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging")
):
    """Regenerate supplier registry from seed data."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    typer.echo("🔄 Regenerating supplier registry...")
    
    try:
        result = registry_only_flow()
        
        typer.echo("✅ Registry regeneration completed successfully!")
        typer.echo(f"📊 Nodes created: {result['nodes_count']}")
        
    except Exception as e:
        typer.echo(f"❌ Registry regeneration failed: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def serve_flows(
    port: int = typer.Option(4200, "--port", "-p", help="Port for Prefect server"),
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host for Prefect server")
):
    """Start Prefect server and serve flows."""
    typer.echo(f"🌐 Starting Prefect server on {host}:{port}...")
    
    # Create deployments
    daily_deployment = Deployment.build_from_flow(
        flow=daily_supply_chain_flow,
        name="daily-supply-chain-analysis",
        schedule=CronSchedule(cron="0 6 * * *", timezone="UTC"),  # Daily at 6 AM UTC
        description="Daily supply chain risk analysis"
    )
    
    registry_deployment = Deployment.build_from_flow(
        flow=registry_only_flow,
        name="registry-only",
        description="Build registry only"
    )
    
    export_deployment = Deployment.build_from_flow(
        flow=export_only_flow,
        name="export-only",
        description="Export CSV only"
    )
    
    # Serve flows
    serve(
        daily_deployment,
        registry_deployment,
        export_deployment,
        limit=1,
        port=port,
        host=host
    )


@app.command()
def check_setup():
    """Check if the system is properly set up."""
    typer.echo("🔍 Checking system setup...")
    
    # Check required directories
    required_dirs = [
        "data/inputs",
        "data/outputs", 
        "cache",
        "logs"
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        typer.echo(f"❌ Missing directories: {missing_dirs}")
        typer.echo("Run 'make setup' to create required directories.")
        raise typer.Exit(1)
    
    # Check required files
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
        typer.echo(f"❌ Missing files: {missing_files}")
        raise typer.Exit(1)
    
    # Check environment variables
    import os
    serp_key = os.getenv('SERP_API_KEY')
    if not serp_key:
        typer.echo("⚠️  SERP_API_KEY not set. Some features may be limited.")
    else:
        typer.echo("✅ SERP_API_KEY is set.")
    
    twitter_token = os.getenv('TWITTER_BEARER_TOKEN')
    if not twitter_token:
        typer.echo("⚠️  TWITTER_BEARER_TOKEN not set. Social media features will be limited.")
    else:
        typer.echo("✅ TWITTER_BEARER_TOKEN is set.")
    
    typer.echo("✅ System setup check completed!")


@app.command()
def test_agents():
    """Test individual agents."""
    typer.echo("🧪 Testing individual agents...")
    
    try:
        # Test registry agent
        typer.echo("Testing registry agent...")
        from agents.agent0_registry import RegistryAgent
        registry_agent = RegistryAgent()
        nodes = registry_agent.run()
        typer.echo(f"✅ Registry agent: {len(nodes)} nodes created")
        
        # Test news agent
        typer.echo("Testing news agent...")
        from agents.agent2_news import NewsAgent
        from core.io import read_yaml
        allowlist = read_yaml("data/inputs/allowlist_regions.yaml")
        news_agent = NewsAgent()
        news_df = news_agent.run(nodes, allowlist)
        typer.echo(f"✅ News agent: {len(news_df)} articles fetched")
        
        # Test weather agent
        typer.echo("Testing weather agent...")
        from agents.agent5_weather import WeatherAgent
        weather_agent = WeatherAgent()
        weather_df = weather_agent.run(nodes)
        typer.echo(f"✅ Weather agent: {len(weather_df)} anomalies detected")
        
        typer.echo("✅ All agent tests completed successfully!")
        
    except Exception as e:
        typer.echo(f"❌ Agent test failed: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
