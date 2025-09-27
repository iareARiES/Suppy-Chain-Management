"""
Agent 1: Social Media Fetcher
Fetch social media data from Twitter/X for supply chain monitoring.
"""
import logging
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import os
import tweepy
import time

from core.models import SocialEvent
from core.io import read_json, write_parquet
from core.utils import now_utc

logger = logging.getLogger(__name__)


class SocialAgent:
    """Agent for fetching social media data from Twitter/X."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        
        if not self.bearer_token:
            logger.warning("No Twitter Bearer Token provided, will use mock data")
            self.client = None
        else:
            try:
                self.client = tweepy.Client(bearer_token=self.bearer_token)
                logger.info("Twitter client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twitter client: {e}")
                self.client = None
    
    def run(self, nodes: List[Dict[str, Any]], allowlist: Dict[str, Any]) -> pd.DataFrame:
        """
        Fetch social media data for all nodes.
        
        Args:
            nodes: List of node dictionaries
            allowlist: Region allowlist configuration
            
        Returns:
            DataFrame with social events
        """
        logger.info("Starting social media agent...")
        
        social_events = []
        
        if not self.client:
            logger.info("Using mock social media data")
            return self._get_mock_social_events(nodes)
        
        for node in nodes:
            try:
                events = self._fetch_node_social_events(node)
                social_events.extend(events)
                
                # Rate limiting - Twitter API has strict limits
                time.sleep(1)
                
            except Exception as e:
                logger.warning(f"Failed to fetch social data for {node.get('name', 'unknown')}: {e}")
        
        # Convert to DataFrame
        if social_events:
            df = pd.DataFrame(social_events)
        else:
            df = pd.DataFrame(columns=[
                'node_id', 'ts', 'handle', 'text', 'url', 'ts_ingested', 
                'sentiment_score', 'engagement_count'
            ])
        
        # Save to parquet
        self._save_social_events(df)
        
        logger.info(f"Social media agent completed. Fetched {len(df)} social events")
        return df
    
    def _fetch_node_social_events(self, node: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch social media events for a specific node.
        
        Args:
            node: Node dictionary
            
        Returns:
            List of social event dictionaries
        """
        events = []
        node_id = node.get('node_id')
        name = node.get('name', '')
        x_handle = node.get('x_handle', '')
        
        if not self.client:
            return events
        
        try:
            # Search for tweets mentioning the company
            search_queries = []
            
            # Add company name
            if name:
                search_queries.append(name)
            
            # Add Twitter handle if available
            if x_handle:
                search_queries.append(f"@{x_handle}")
            
            # Add ticker if available
            ticker = node.get('ticker')
            if ticker:
                search_queries.append(f"${ticker}")
            
            for query in search_queries[:2]:  # Limit to 2 queries per node
                try:
                    # Search for recent tweets (last 7 days)
                    tweets = self.client.search_recent_tweets(
                        query=query,
                        max_results=10,
                        tweet_fields=['created_at', 'public_metrics', 'context_annotations'],
                        user_fields=['username'],
                        expansions=['author_id']
                    )
                    
                    if tweets.data:
                        for tweet in tweets.data:
                            # Get user info
                            user = None
                            if tweets.includes and 'users' in tweets.includes:
                                user = next((u for u in tweets.includes['users'] if u.id == tweet.author_id), None)
                            
                            # Calculate engagement
                            metrics = tweet.public_metrics or {}
                            engagement = (
                                metrics.get('like_count', 0) + 
                                metrics.get('retweet_count', 0) + 
                                metrics.get('reply_count', 0)
                            )
                            
                            # Only include tweets with some engagement
                            if engagement > 0:
                                event = {
                                    'node_id': node_id,
                                    'ts': tweet.created_at,
                                    'handle': user.username if user else 'unknown',
                                    'text': tweet.text,
                                    'url': f"https://twitter.com/{user.username if user else 'unknown'}/status/{tweet.id}",
                                    'ts_ingested': now_utc(),
                                    'sentiment_score': None,  # Would need sentiment analysis
                                    'engagement_count': engagement
                                }
                                events.append(event)
                    
                    # Rate limiting
                    time.sleep(2)
                    
                except Exception as e:
                    logger.warning(f"Failed to search tweets for query '{query}': {e}")
                    continue
        
        except Exception as e:
            logger.warning(f"Failed to fetch social events for {node_id}: {e}")
        
        return events
    
    def _get_mock_social_events(self, nodes: List[Dict[str, Any]]) -> pd.DataFrame:
        """Get mock social media events for demo purposes."""
        mock_events = []
        
        for i, node in enumerate(nodes[:5]):  # Limit to first 5 nodes
            # Generate 2-3 mock events per node
            for j in range(2):
                event = {
                    'node_id': node['node_id'],
                    'ts': now_utc() - timedelta(hours=random.randint(1, 168)),  # Last week
                    'handle': f"user_{i}_{j}",
                    'text': f"Mock tweet about {node['name']} - supply chain update #{j+1}",
                    'url': f"https://twitter.com/user_{i}_{j}/status/{random.randint(100000, 999999)}",
                    'ts_ingested': now_utc(),
                    'sentiment_score': random.uniform(-0.5, 0.5),
                    'engagement_count': random.randint(5, 100)
                }
                mock_events.append(event)
        
        df = pd.DataFrame(mock_events)
        self._save_social_events(df)
        return df
    
    def _save_social_events(self, df: pd.DataFrame) -> None:
        """Save social events to parquet file."""
        output_path = self.data_dir / "outputs" / "social_events.parquet"
        write_parquet(df, str(output_path))
        logger.info(f"Saved {len(df)} social events to {output_path}")


def main():
    """Main function for running the social media agent."""
    # Load nodes
    nodes = read_json("data/outputs/nodes.json")
    allowlist = read_yaml("data/inputs/allowlist_regions.yaml")
    
    agent = SocialAgent()
    df = agent.run(nodes, allowlist)
    print(f"Social media agent completed. Fetched {len(df)} social events.")


if __name__ == "__main__":
    import random
    from core.io import read_yaml
    main()
