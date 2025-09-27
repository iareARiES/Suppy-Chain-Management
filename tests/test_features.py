"""
Tests for the feature building agent.
"""
import pytest
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

from agents.agent6_features import FeatureAgent
from core.utils import now_utc


class TestFeatureAgent:
    """Test cases for FeatureAgent."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_nodes(self):
        """Create sample nodes for testing."""
        return [
            {
                'node_id': 'CN-GD_Shenzhen_Test-Supplier_22.54_114.06',
                'node_type': 'supplier',
                'name': 'Test Supplier',
                'country': 'China',
                'city': 'Shenzhen',
                'lat': 22.54,
                'lon': 114.06,
                'tier': 1.0,
                'category': 'PCB',
                'region': 'china'
            }
        ]
    
    @pytest.fixture
    def sample_news_data(self, temp_dir):
        """Create sample news data for testing."""
        now = now_utc()
        news_data = {
            'node_id': ['CN-GD_Shenzhen_Test-Supplier_22.54_114.06'] * 5,
            'url': [f'https://test.com/news{i}' for i in range(5)],
            'headline': [f'Test News {i}' for i in range(5)],
            'snippet': [f'Test snippet {i}' for i in range(5)],
            'outlet': ['testnews.com'] * 5,
            'ts': [now - timedelta(hours=i) for i in range(5)],
            'sentiment_score': [0.1, -0.5, 0.3, -0.2, 0.0],
            'source': ['rss'] * 5
        }
        
        news_df = pd.DataFrame(news_data)
        news_path = Path(temp_dir) / "outputs" / "news_events.parquet"
        news_path.parent.mkdir(parents=True, exist_ok=True)
        news_df.to_parquet(news_path, index=False)
        
        return news_df
    
    @pytest.fixture
    def sample_events_data(self, temp_dir):
        """Create sample events data for testing."""
        now = now_utc()
        events_data = {
            'node_id': ['CN-GD_Shenzhen_Test-Supplier_22.54_114.06'],
            'event_type': ['strike'],
            'ts_event': [now - timedelta(days=1)],
            'severity': ['medium'],
            'duration_h': [24.0],
            'geo_text': ['Shenzhen'],
            'source_url': ['https://test.com/strike'],
            'extracted_text': ['Labor strike reported at facility'],
            'confidence': [0.8]
        }
        
        events_df = pd.DataFrame(events_data)
        events_path = Path(temp_dir) / "outputs" / "extracted_events.parquet"
        events_path.parent.mkdir(parents=True, exist_ok=True)
        events_df.to_parquet(events_path, index=False)
        
        return events_df
    
    @pytest.fixture
    def sample_weather_data(self, temp_dir):
        """Create sample weather data for testing."""
        now = now_utc()
        weather_data = {
            'node_id': ['CN-GD_Shenzhen_Test-Supplier_22.54_114.06'],
            'ts': [now - timedelta(days=1)],
            'anomaly_type': ['heavy_precip'],
            'severity': ['high'],
            'value': [50.0],
            'threshold': [40.0],
            'duration_h': [24.0]
        }
        
        weather_df = pd.DataFrame(weather_data)
        weather_path = Path(temp_dir) / "outputs" / "weather_anomalies.parquet"
        weather_path.parent.mkdir(parents=True, exist_ok=True)
        weather_df.to_parquet(weather_path, index=False)
        
        return weather_df
    
    def test_feature_agent_initialization(self, temp_dir):
        """Test FeatureAgent initialization."""
        agent = FeatureAgent(data_dir=temp_dir)
        assert agent.data_dir == Path(temp_dir)
    
    def test_load_news_data(self, temp_dir, sample_news_data):
        """Test loading news data."""
        agent = FeatureAgent(data_dir=temp_dir)
        news_df = agent._load_news_data()
        
        assert len(news_df) == 5
        assert 'node_id' in news_df.columns
        assert 'sentiment_score' in news_df.columns
    
    def test_load_events_data(self, temp_dir, sample_events_data):
        """Test loading events data."""
        agent = FeatureAgent(data_dir=temp_dir)
        events_df = agent._load_events_data()
        
        assert len(events_df) == 1
        assert 'event_type' in events_df.columns
        assert events_df.iloc[0]['event_type'] == 'strike'
    
    def test_load_weather_data(self, temp_dir, sample_weather_data):
        """Test loading weather data."""
        agent = FeatureAgent(data_dir=temp_dir)
        weather_df = agent._load_weather_data()
        
        assert len(weather_df) == 1
        assert 'anomaly_type' in weather_df.columns
        assert weather_df.iloc[0]['anomaly_type'] == 'heavy_precip'
    
    def test_compute_news_features(self, temp_dir, sample_news_data):
        """Test computing news features."""
        agent = FeatureAgent(data_dir=temp_dir)
        node_id = 'CN-GD_Shenzhen_Test-Supplier_22.54_114.06'
        now = now_utc()
        
        features = agent._compute_news_features(node_id, sample_news_data, now)
        
        assert 'news_count_1d' in features
        assert 'news_count_7d' in features
        assert 'neg_tone_frac_3d' in features
        assert 'news_velocity' in features
        
        # Should have 5 news articles in the last 7 days
        assert features['news_count_7d'] == 5
        # Should have 1 news article in the last 1 day
        assert features['news_count_1d'] == 1
    
    def test_compute_event_features(self, temp_dir, sample_events_data):
        """Test computing event features."""
        agent = FeatureAgent(data_dir=temp_dir)
        node_id = 'CN-GD_Shenzhen_Test-Supplier_22.54_114.06'
        now = now_utc()
        
        features = agent._compute_event_features(node_id, sample_events_data, now)
        
        assert 'strike_flag_7d' in features
        # Should have strike flag set to 1 due to recent strike event
        assert features['strike_flag_7d'] == 1
    
    def test_compute_weather_features(self, temp_dir, sample_weather_data):
        """Test computing weather features."""
        agent = FeatureAgent(data_dir=temp_dir)
        node_id = 'CN-GD_Shenzhen_Test-Supplier_22.54_114.06'
        now = now_utc()
        
        features = agent._compute_weather_features(node_id, sample_weather_data, now)
        
        assert 'weather_anomaly_7d' in features
        # Should have weather anomaly flag set to 1 due to recent anomaly
        assert features['weather_anomaly_7d'] == 1
    
    def test_compute_operational_features(self, temp_dir):
        """Test computing operational features."""
        agent = FeatureAgent(data_dir=temp_dir)
        node = {'node_id': 'test_node'}
        
        features = agent._compute_operational_features(node)
        
        assert 'avg_lead_time_days' in features
        assert 'inventory_days' in features
        assert 'single_sourced' in features
        assert 'past_delay_days' in features
        assert 'disruption_within_7d' in features
        assert 'days_to_disruption' in features
        
        # Check default values
        assert features['single_sourced'] == 0
        assert features['past_delay_days'] == 0
        assert features['avg_lead_time_days'] is None
        assert features['inventory_days'] is None
    
    def test_ensure_schema(self, temp_dir):
        """Test schema enforcement."""
        agent = FeatureAgent(data_dir=temp_dir)
        
        # Create DataFrame with missing columns
        incomplete_df = pd.DataFrame({
            'node_id': ['test_node'],
            'name': ['Test Supplier'],
            'country': ['China']
        })
        
        # Ensure schema
        complete_df = agent._ensure_schema(incomplete_df)
        
        # Check that all required columns are present
        required_columns = [
            'node_id', 'node_type', 'name', 'country', 'lat', 'lon', 'tier',
            'news_count_1d', 'news_count_7d', 'neg_tone_frac_3d',
            'weather_anomaly_7d', 'strike_flag_7d', 'avg_lead_time_days',
            'inventory_days', 'single_sourced', 'past_delay_days',
            'news_velocity', 'disruption_within_7d', 'days_to_disruption'
        ]
        
        for col in required_columns:
            assert col in complete_df.columns
        
        # Check data types
        assert complete_df['news_count_1d'].dtype == 'int64'
        assert complete_df['neg_tone_frac_3d'].dtype == 'float64'
        assert complete_df['lat'].dtype == 'float64'
    
    def test_build_node_features(self, temp_dir, sample_nodes, sample_news_data, 
                                sample_events_data, sample_weather_data):
        """Test building features for a single node."""
        agent = FeatureAgent(data_dir=temp_dir)
        node = sample_nodes[0]
        
        # Create empty DataFrames for missing data
        empty_social_df = pd.DataFrame()
        empty_market_df = pd.DataFrame()
        
        features = agent._build_node_features(
            node, sample_news_data, empty_social_df, 
            sample_events_data, sample_weather_data, empty_market_df
        )
        
        # Check that all required features are present
        assert 'node_id' in features
        assert 'name' in features
        assert 'country' in features
        assert 'lat' in features
        assert 'lon' in features
        assert 'tier' in features
        
        # Check computed features
        assert 'news_count_1d' in features
        assert 'news_count_7d' in features
        assert 'neg_tone_frac_3d' in features
        assert 'strike_flag_7d' in features
        assert 'weather_anomaly_7d' in features
        assert 'news_velocity' in features
        
        # Check operational features
        assert 'avg_lead_time_days' in features
        assert 'inventory_days' in features
        assert 'single_sourced' in features
        assert 'past_delay_days' in features
    
    def test_run_complete_flow(self, temp_dir, sample_nodes, sample_news_data,
                              sample_events_data, sample_weather_data):
        """Test complete feature building flow."""
        agent = FeatureAgent(data_dir=temp_dir)
        
        # Create empty DataFrames for missing data
        empty_social_df = pd.DataFrame()
        empty_market_df = pd.DataFrame()
        
        # Save empty DataFrames to expected locations
        social_path = Path(temp_dir) / "outputs" / "social_events.parquet"
        social_path.parent.mkdir(parents=True, exist_ok=True)
        empty_social_df.to_parquet(social_path, index=False)
        
        market_path = Path(temp_dir) / "outputs" / "market_signals.parquet"
        market_path.parent.mkdir(parents=True, exist_ok=True)
        empty_market_df.to_parquet(market_path, index=False)
        
        features_df = agent.run(sample_nodes)
        
        assert len(features_df) == 1
        assert len(features_df.columns) >= 19  # All required columns
        
        # Check that the node features are correctly computed
        row = features_df.iloc[0]
        assert row['node_id'] == 'CN-GD_Shenzhen_Test-Supplier_22.54_114.06'
        assert row['name'] == 'Test Supplier'
        assert row['country'] == 'China'
        assert row['news_count_7d'] == 5
        assert row['strike_flag_7d'] == 1
        assert row['weather_anomaly_7d'] == 1
