"""
Agent 4: Deep Crawl and Event Extraction
Use crawl4ai to extract structured events from news articles and company websites.
"""
import logging
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import os
import re
import json

from core.models import ExtractedEvent
from core.io import read_json, read_parquet, write_parquet
from core.utils import now_utc

logger = logging.getLogger(__name__)


class CrawlAgent:
    """Agent for deep crawling and event extraction."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.crawl4ai_available = self._check_crawl4ai()
        
        if not self.crawl4ai_available:
            logger.warning("crawl4ai not available, will use mock data")
    
    def _check_crawl4ai(self) -> bool:
        """Check if crawl4ai is available."""
        try:
            import crawl4ai
            return True
        except ImportError:
            return False
    
    def run(self, nodes: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Crawl URLs and extract events.
        
        Args:
            nodes: List of node dictionaries
            
        Returns:
            DataFrame with extracted events
        """
        logger.info("Starting crawl and extract agent...")
        
        extracted_events = []
        
        if not self.crawl4ai_available:
            logger.info("Using mock extracted events")
            return self._get_mock_extracted_events(nodes)
        
        # Load news events to get URLs to crawl
        news_df = self._load_news_events()
        
        # Get unique URLs from news events
        urls_to_crawl = news_df['url'].unique().tolist() if not news_df.empty else []
        
        # Add company website URLs from nodes
        for node in nodes:
            if node.get('site_url'):
                urls_to_crawl.append(node['site_url'])
            if node.get('alt_url'):
                urls_to_crawl.append(node['alt_url'])
        
        # Limit to reasonable number of URLs
        urls_to_crawl = urls_to_crawl[:50]
        
        for url in urls_to_crawl:
            try:
                events = self._crawl_and_extract_events(url, nodes)
                extracted_events.extend(events)
                
                # Rate limiting
                import time
                time.sleep(2)
                
            except Exception as e:
                logger.warning(f"Failed to crawl {url}: {e}")
        
        # Convert to DataFrame
        if extracted_events:
            df = pd.DataFrame(extracted_events)
        else:
            df = pd.DataFrame(columns=[
                'node_id', 'event_type', 'ts_event', 'severity', 'duration_h',
                'geo_text', 'source_url', 'extracted_text', 'confidence'
            ])
        
        # Save to parquet
        self._save_extracted_events(df)
        
        logger.info(f"Crawl and extract agent completed. Extracted {len(df)} events")
        return df
    
    def _load_news_events(self) -> pd.DataFrame:
        """Load news events to get URLs for crawling."""
        news_path = self.data_dir / "outputs" / "news_events.parquet"
        try:
            return read_parquet(str(news_path))
        except FileNotFoundError:
            logger.warning("News events file not found, skipping URL extraction")
            return pd.DataFrame()
    
    def _crawl_and_extract_events(self, url: str, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Crawl a URL and extract events.
        
        Args:
            url: URL to crawl
            nodes: List of nodes for context
            
        Returns:
            List of extracted event dictionaries
        """
        events = []
        
        try:
            from crawl4ai import AsyncWebCrawler
            
            # This would be async in real implementation
            # For now, we'll simulate the crawling process
            
            # Simulate extracted content
            extracted_content = self._simulate_crawl_content(url)
            
            # Extract events from content
            events = self._extract_events_from_content(extracted_content, url, nodes)
            
        except Exception as e:
            logger.warning(f"Failed to crawl {url}: {e}")
        
        return events
    
    def _simulate_crawl_content(self, url: str) -> str:
        """Simulate crawled content for demo purposes."""
        # This would be replaced with actual crawl4ai implementation
        mock_content = f"""
        Company Update: Recent developments at our manufacturing facility.
        Production has been temporarily halted due to equipment maintenance.
        Expected to resume operations within 48 hours.
        
        Weather Alert: Severe weather conditions affecting transportation routes.
        Alternative routes have been activated to ensure delivery continuity.
        
        Labor Update: Union negotiations continue with positive progress.
        No disruptions to current operations expected.
        """
        return mock_content
    
    def _extract_events_from_content(self, content: str, url: str, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract events from crawled content.
        
        Args:
            content: Crawled content text
            url: Source URL
            nodes: List of nodes for context
            
        Returns:
            List of extracted event dictionaries
        """
        events = []
        
        # Simple pattern matching for event extraction
        # In a real implementation, this would use NLP/ML models
        
        # Find relevant node for this URL
        relevant_node = self._find_relevant_node(url, nodes)
        if not relevant_node:
            return events
        
        node_id = relevant_node['node_id']
        
        # Event patterns
        event_patterns = {
            'shutdown': [
                r'halted|stopped|shutdown|suspended',
                r'production.*stop|manufacturing.*halt',
                r'facility.*closed|plant.*shutdown'
            ],
            'strike': [
                r'strike|labor.*dispute|union.*action',
                r'work.*stoppage|industrial.*action'
            ],
            'fire': [
                r'fire|blaze|burning|combustion',
                r'fire.*damage|fire.*incident'
            ],
            'flood': [
                r'flood|flooding|water.*damage',
                r'heavy.*rain|storm.*damage'
            ],
            'inspection': [
                r'inspection|audit|compliance.*check',
                r'regulatory.*review|safety.*inspection'
            ],
            'outage': [
                r'outage|power.*failure|electrical.*issue',
                r'equipment.*failure|system.*down'
            ],
            'policy': [
                r'policy.*change|regulation.*update',
                r'compliance.*requirement|new.*rule'
            ],
            'M&A': [
                r'acquisition|merger|takeover',
                r'buyout|consolidation|partnership'
            ]
        }
        
        # Check for each event type
        for event_type, patterns in event_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    # Determine severity based on context
                    severity = self._determine_severity(content, event_type)
                    
                    # Calculate confidence based on pattern match strength
                    confidence = self._calculate_confidence(content, pattern)
                    
                    event = {
                        'node_id': node_id,
                        'event_type': event_type,
                        'ts_event': now_utc(),
                        'severity': severity,
                        'duration_h': self._estimate_duration(content, event_type),
                        'geo_text': self._extract_location(content),
                        'source_url': url,
                        'extracted_text': content[:500],  # First 500 chars
                        'confidence': confidence
                    }
                    events.append(event)
                    break  # Only one event per type per content
        
        return events
    
    def _find_relevant_node(self, url: str, nodes: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find the most relevant node for a given URL."""
        # Simple matching based on domain or company name
        for node in nodes:
            if node.get('site_url') and node['site_url'] in url:
                return node
            if node.get('alt_url') and node['alt_url'] in url:
                return node
        
        # If no direct match, return first node as fallback
        return nodes[0] if nodes else None
    
    def _determine_severity(self, content: str, event_type: str) -> str:
        """Determine event severity based on content."""
        high_severity_words = ['critical', 'severe', 'major', 'significant', 'emergency']
        medium_severity_words = ['moderate', 'noticeable', 'concerning', 'important']
        
        content_lower = content.lower()
        
        if any(word in content_lower for word in high_severity_words):
            return 'high'
        elif any(word in content_lower for word in medium_severity_words):
            return 'medium'
        else:
            return 'low'
    
    def _calculate_confidence(self, content: str, pattern: str) -> float:
        """Calculate confidence score for event extraction."""
        # Simple confidence based on pattern match strength
        matches = len(re.findall(pattern, content, re.IGNORECASE))
        return min(0.9, 0.5 + (matches * 0.1))
    
    def _estimate_duration(self, content: str, event_type: str) -> Optional[float]:
        """Estimate event duration from content."""
        # Look for duration indicators
        duration_patterns = [
            r'(\d+)\s*hours?',
            r'(\d+)\s*days?',
            r'(\d+)\s*weeks?'
        ]
        
        for pattern in duration_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                value = float(match.group(1))
                if 'hour' in pattern:
                    return value
                elif 'day' in pattern:
                    return value * 24
                elif 'week' in pattern:
                    return value * 24 * 7
        
        # Default durations by event type
        default_durations = {
            'shutdown': 24.0,
            'strike': 168.0,  # 1 week
            'fire': 48.0,
            'flood': 72.0,
            'inspection': 8.0,
            'outage': 12.0,
            'policy': None,
            'M&A': None
        }
        
        return default_durations.get(event_type)
    
    def _extract_location(self, content: str) -> Optional[str]:
        """Extract location information from content."""
        # Simple location extraction
        location_patterns = [
            r'in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'at\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'facility\s+in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        return None
    
    def _get_mock_extracted_events(self, nodes: List[Dict[str, Any]]) -> pd.DataFrame:
        """Get mock extracted events for demo purposes."""
        import random
        
        mock_events = []
        event_types = ['shutdown', 'strike', 'fire', 'flood', 'inspection', 'outage', 'policy', 'M&A']
        
        for i, node in enumerate(nodes[:10]):  # Limit to first 10 nodes
            # Generate 1-2 mock events per node
            num_events = random.randint(1, 2)
            for j in range(num_events):
                event_type = random.choice(event_types)
                severity = random.choice(['low', 'medium', 'high'])
                
                event = {
                    'node_id': node['node_id'],
                    'event_type': event_type,
                    'ts_event': now_utc() - timedelta(hours=random.randint(1, 168)),
                    'severity': severity,
                    'duration_h': random.uniform(1, 72) if event_type in ['shutdown', 'outage'] else None,
                    'geo_text': f"Location {i+1}",
                    'source_url': f"https://example.com/news/{i}_{j}",
                    'extracted_text': f"Mock extracted text about {event_type} at {node['name']}",
                    'confidence': random.uniform(0.6, 0.9)
                }
                mock_events.append(event)
        
        df = pd.DataFrame(mock_events)
        self._save_extracted_events(df)
        return df
    
    def _save_extracted_events(self, df: pd.DataFrame) -> None:
        """Save extracted events to parquet file."""
        output_path = self.data_dir / "outputs" / "extracted_events.parquet"
        write_parquet(df, str(output_path))
        logger.info(f"Saved {len(df)} extracted events to {output_path}")


def main():
    """Main function for running the crawl agent."""
    # Load nodes
    nodes = read_json("data/outputs/nodes.json")
    
    agent = CrawlAgent()
    df = agent.run(nodes)
    print(f"Crawl agent completed. Extracted {len(df)} events.")


if __name__ == "__main__":
    main()
