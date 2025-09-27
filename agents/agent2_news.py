"""
Agent 2: News Fetcher
Pull RSS feeds and use SERP API to discover fresh articles.
"""
import logging
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
import os

from core.models import NewsEvent
from core.news import NewsAggregator
from core.io import read_json, write_parquet, read_yaml
from core.utils import now_utc, deduplicate_by_url

logger = logging.getLogger(__name__)


class NewsAgent:
    """Agent for fetching news from RSS feeds and SERP API."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.serp_api_key = os.getenv('SERP_API_KEY')
        
        if not self.serp_api_key:
            logger.warning("No SERP API key provided, will only fetch RSS feeds")
        
        self.news_aggregator = NewsAggregator(self.serp_api_key) if self.serp_api_key else None
    
    def run(self, nodes: List[Dict[str, Any]], allowlist: Dict[str, Any]) -> pd.DataFrame:
        """
        Fetch news from RSS feeds and SERP API.
        
        Args:
            nodes: List of node dictionaries
            allowlist: Region allowlist configuration
            
        Returns:
            DataFrame with news events
        """
        logger.info("Starting news agent...")
        
        all_articles = []
        
        # Fetch RSS feeds
        rss_articles = self._fetch_rss_feeds(allowlist)
        all_articles.extend(rss_articles)
        logger.info(f"Fetched {len(rss_articles)} articles from RSS feeds")
        
        # Fetch SERP results if API key available
        if self.news_aggregator:
            serp_articles = self._fetch_serp_results(nodes, allowlist)
            all_articles.extend(serp_articles)
            logger.info(f"Fetched {len(serp_articles)} articles from SERP API")
        
        # Convert to DataFrame
        if all_articles:
            df = pd.DataFrame(all_articles)
            df['ts_ingested'] = now_utc()
            
            # Deduplicate by URL
            df = deduplicate_by_url(df, 'url')
            
            # Add sentiment scores
            df = self._add_sentiment_scores(df)
            
        else:
            df = pd.DataFrame(columns=[
                'url', 'headline', 'snippet', 'outlet', 'ts', 'source', 
                'region', 'ts_ingested', 'sentiment_score'
            ])
        
        # Save to parquet
        self._save_news_events(df)
        
        logger.info(f"News agent completed. Fetched {len(df)} unique news articles")
        return df
    
    def _fetch_rss_feeds(self, allowlist: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch articles from RSS feeds in allowlist.
        
        Args:
            allowlist: Region allowlist configuration
            
        Returns:
            List of article dictionaries
        """
        if not self.news_aggregator:
            return []
        
        articles = self.news_aggregator.fetch_rss_allowlist(allowlist)
        
        # Add node_id as 'unknown' for RSS articles (they're general news)
        for article in articles:
            article['node_id'] = 'unknown'
        
        return articles
    
    def _fetch_serp_results(self, nodes: List[Dict[str, Any]], allowlist: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch articles using SERP API for each node.
        
        Args:
            nodes: List of node dictionaries
            allowlist: Region allowlist configuration
            
        Returns:
            List of article dictionaries
        """
        if not self.news_aggregator:
            return []
        
        all_articles = []
        
        for node in nodes:
            try:
                articles = self.news_aggregator.serp_discover(node, allowlist)
                
                # Add node_id to each article
                node_id = node.get('node_id', 'unknown')
                for article in articles:
                    article['node_id'] = node_id
                
                all_articles.extend(articles)
                
                # Add polite delay between requests
                import time
                time.sleep(1)
                
            except Exception as e:
                logger.warning(f"Failed to fetch SERP results for {node.get('name', 'unknown')}: {e}")
        
        return all_articles
    
    def _add_sentiment_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add sentiment scores to news articles.
        
        Args:
            df: DataFrame with news articles
            
        Returns:
            DataFrame with sentiment scores added
        """
        from core.nlp import get_sentiment_analyzer
        
        sentiment_analyzer = get_sentiment_analyzer()
        
        # Combine headline and snippet for sentiment analysis
        df['combined_text'] = df['headline'].fillna('') + ' ' + df['snippet'].fillna('')
        
        # Calculate sentiment scores
        sentiment_scores = []
        for text in df['combined_text']:
            if len(text.strip()) > 10:
                score = sentiment_analyzer.analyze_sentiment(text)
                sentiment_scores.append(score)
            else:
                sentiment_scores.append(0.0)
        
        df['sentiment_score'] = sentiment_scores
        
        # Remove temporary column
        df = df.drop(columns=['combined_text'])
        
        return df
    
    def _save_news_events(self, df: pd.DataFrame) -> None:
        """Save news events to parquet file."""
        output_path = self.data_dir / "outputs" / "news_events.parquet"
        write_parquet(df, str(output_path))
        logger.info(f"Saved {len(df)} news events to {output_path}")


def main():
    """Main function for running the news agent."""
    # Load nodes and allowlist
    nodes = read_json("data/outputs/nodes.json")
    allowlist = read_yaml("data/inputs/allowlist_regions.yaml")
    
    agent = NewsAgent()
    df = agent.run(nodes, allowlist)
    print(f"News agent completed. Fetched {len(df)} news articles.")


if __name__ == "__main__":
    main()
