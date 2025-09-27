"""
Daily Prefect flow for running all supply chain agents.
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from prefect import flow, task, get_run_logger
from prefect.task_runners import ConcurrentTaskRunner

from agents.agent0_registry import RegistryAgent
from agents.agent1_social import SocialAgent
from agents.agent2_news import NewsAgent
from agents.agent4_crawl import CrawlAgent
from agents.agent5_weather import WeatherAgent
from agents.agent6_features import FeatureAgent
from agents.agent7_export import ExportAgent

from core.io import read_json, read_yaml

logger = logging.getLogger(__name__)


@task(name="build_registry")
def build_registry_task() -> List[Dict[str, Any]]:
    """Build supplier registry from seed data."""
    logger = get_run_logger()
    logger.info("Starting registry build task...")
    
    agent = RegistryAgent()
    nodes = agent.run()
    
    logger.info(f"Registry build completed. Created {len(nodes)} nodes.")
    return nodes


@task(name="fetch_social")
def fetch_social_task(nodes: List[Dict[str, Any]], allowlist: Dict[str, Any]) -> Any:
    """Fetch social media data."""
    logger = get_run_logger()
    logger.info("Starting social media fetch task...")
    
    agent = SocialAgent()
    df = agent.run(nodes, allowlist)
    
    logger.info(f"Social media fetch completed. Fetched {len(df)} social events.")
    return df


@task(name="fetch_news")
def fetch_news_task(nodes: List[Dict[str, Any]], allowlist: Dict[str, Any]) -> Any:
    """Fetch news data from RSS and SERP."""
    logger = get_run_logger()
    logger.info("Starting news fetch task...")
    
    agent = NewsAgent()
    df = agent.run(nodes, allowlist)
    
    logger.info(f"News fetch completed. Fetched {len(df)} news articles.")
    return df




@task(name="crawl_extract")
def crawl_extract_task(nodes: List[Dict[str, Any]]) -> Any:
    """Crawl URLs and extract events."""
    logger = get_run_logger()
    logger.info("Starting crawl and extract task...")
    
    agent = CrawlAgent()
    df = agent.run(nodes)
    
    logger.info(f"Crawl and extract completed. Extracted {len(df)} events.")
    return df


@task(name="fetch_weather")
def fetch_weather_task(nodes: List[Dict[str, Any]]) -> Any:
    """Fetch weather data and detect anomalies."""
    logger = get_run_logger()
    logger.info("Starting weather fetch task...")
    
    agent = WeatherAgent()
    df = agent.run(nodes)
    
    logger.info(f"Weather fetch completed. Detected {len(df)} weather anomalies.")
    return df


@task(name="build_features")
def build_features_task(nodes: List[Dict[str, Any]]) -> Any:
    """Build ML features from all data sources."""
    logger = get_run_logger()
    logger.info("Starting feature build task...")
    
    agent = FeatureAgent()
    df = agent.run(nodes)
    
    logger.info(f"Feature build completed. Built features for {len(df)} nodes.")
    return df


@task(name="export_csv")
def export_csv_task(features_df: Any) -> str:
    """Export final features CSV."""
    logger = get_run_logger()
    logger.info("Starting CSV export task...")
    
    agent = ExportAgent()
    output_path = agent.run(features_df)
    
    logger.info(f"CSV export completed. Exported to {output_path}")
    return output_path


@flow(
    name="supply-chain-daily-flow",
    task_runner=ConcurrentTaskRunner(),
    description="Daily supply chain risk analysis pipeline"
)
def daily_supply_chain_flow():
    """
    Main Prefect flow for daily supply chain risk analysis.
    
    This flow orchestrates all agents in the correct order:
    1. Build registry from seed suppliers
    2. Fetch social media data
    3. Fetch news data
    4. Fetch market data
    5. Crawl and extract events
    6. Fetch weather data
    7. Build ML features
    8. Export final CSV
    """
    logger = get_run_logger()
    logger.info("Starting daily supply chain risk analysis flow...")
    
    # Load allowlist configuration
    allowlist_path = Path("data/inputs/allowlist_regions.yaml")
    allowlist = read_yaml(str(allowlist_path))
    
    # Step 1: Build registry
    nodes = build_registry_task()
    
    # Steps 2-5: Run data collection agents in parallel where possible
    social_future = fetch_social_task.submit(nodes, allowlist)
    news_future = fetch_news_task.submit(nodes, allowlist)
    weather_future = fetch_weather_task.submit(nodes)
    
    # Wait for data collection to complete
    social_df = social_future.result()
    news_df = news_future.result()
    weather_df = weather_future.result()
    
    # Step 5: Crawl and extract (depends on news/social data)
    crawl_future = crawl_extract_task.submit(nodes)
    crawl_df = crawl_future.result()
    
    # Step 7: Build features (depends on all data)
    features_future = build_features_task.submit(nodes)
    features_df = features_future.result()
    
    # Step 8: Export CSV
    output_path = export_csv_task.submit(features_df).result()
    
    logger.info(f"Daily supply chain flow completed successfully!")
    logger.info(f"Final output: {output_path}")
    
    return {
        "nodes_count": len(nodes),
        "social_events": len(social_df),
        "news_articles": len(news_df),
        "extracted_events": len(crawl_df),
        "weather_anomalies": len(weather_df),
        "feature_rows": len(features_df),
        "output_path": output_path
    }


@flow(
    name="supply-chain-registry-only",
    description="Build registry only (for testing or updates)"
)
def registry_only_flow():
    """Flow to build registry only."""
    logger = get_run_logger()
    logger.info("Starting registry-only flow...")
    
    nodes = build_registry_task()
    
    logger.info(f"Registry-only flow completed. Created {len(nodes)} nodes.")
    return {"nodes_count": len(nodes)}


@flow(
    name="supply-chain-export-only",
    description="Export CSV only (assumes features already built)"
)
def export_only_flow():
    """Flow to export CSV only."""
    logger = get_run_logger()
    logger.info("Starting export-only flow...")
    
    # Load nodes
    nodes_path = Path("data/outputs/nodes.json")
    nodes = read_json(str(nodes_path))
    
    # Build features
    features_df = build_features_task(nodes)
    
    # Export CSV
    output_path = export_csv_task(features_df)
    
    logger.info(f"Export-only flow completed. Exported to {output_path}")
    return {"output_path": output_path}


if __name__ == "__main__":
    # Run the daily flow
    result = daily_supply_chain_flow()
    print(f"Flow completed with result: {result}")
