"""
Tests for the registry agent.
"""
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil

from agents.agent0_registry import RegistryAgent
from core.io import read_json


class TestRegistryAgent:
    """Test cases for RegistryAgent."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_suppliers(self, temp_dir):
        """Create sample suppliers CSV for testing."""
        suppliers_data = {
            'name': ['Test Supplier 1', 'Test Supplier 2'],
            'category': ['PCB', 'EMS'],
            'site_url': ['https://test1.com', 'https://test2.com'],
            'alt_url': ['', 'https://test2-alt.com'],
            'x_handle': ['@test1', ''],
            'ticker': ['TEST1', 'TEST2'],
            'region': ['china', 'taiwan'],
            'city': ['Shanghai', 'Taipei'],
            'country': ['China', 'Taiwan']
        }
        
        suppliers_df = pd.DataFrame(suppliers_data)
        suppliers_path = Path(temp_dir) / "suppliers_seed.csv"
        suppliers_df.to_csv(suppliers_path, index=False)
        
        return str(suppliers_path)
    
    @pytest.fixture
    def sample_allowlist(self, temp_dir):
        """Create sample allowlist YAML for testing."""
        allowlist_data = {
            'regions': {
                'china': {
                    'name': 'China',
                    'outlets': [
                        {
                            'name': 'Test News China',
                            'domain': 'testnews.cn',
                            'rss': 'https://testnews.cn/rss',
                            'x_handle': '@testnewschina'
                        }
                    ]
                },
                'taiwan': {
                    'name': 'Taiwan',
                    'outlets': [
                        {
                            'name': 'Test News Taiwan',
                            'domain': 'testnews.tw',
                            'rss': 'https://testnews.tw/rss',
                            'x_handle': '@testnewstaiwan'
                        }
                    ]
                }
            }
        }
        
        import yaml
        allowlist_path = Path(temp_dir) / "allowlist_regions.yaml"
        with open(allowlist_path, 'w') as f:
            yaml.dump(allowlist_data, f)
        
        return str(allowlist_path)
    
    def test_registry_agent_initialization(self, temp_dir):
        """Test RegistryAgent initialization."""
        agent = RegistryAgent(data_dir=temp_dir)
        assert agent.data_dir == Path(temp_dir)
        assert agent.geocoder is not None
    
    def test_load_suppliers(self, temp_dir, sample_suppliers):
        """Test loading suppliers from CSV."""
        agent = RegistryAgent(data_dir=temp_dir)
        
        # Copy sample suppliers to expected location
        import shutil
        shutil.copy(sample_suppliers, Path(temp_dir) / "inputs" / "suppliers_seed.csv")
        
        suppliers_df = agent._load_suppliers()
        
        assert len(suppliers_df) == 2
        assert 'name' in suppliers_df.columns
        assert 'country' in suppliers_df.columns
        assert suppliers_df.iloc[0]['name'] == 'Test Supplier 1'
    
    def test_load_allowlist(self, temp_dir, sample_allowlist):
        """Test loading allowlist from YAML."""
        agent = RegistryAgent(data_dir=temp_dir)
        
        # Copy sample allowlist to expected location
        import shutil
        Path(temp_dir).mkdir(parents=True, exist_ok=True)
        Path(temp_dir / "inputs").mkdir(parents=True, exist_ok=True)
        shutil.copy(sample_allowlist, Path(temp_dir) / "inputs" / "allowlist_regions.yaml")
        
        allowlist = agent._load_allowlist()
        
        assert 'regions' in allowlist
        assert 'china' in allowlist['regions']
        assert 'taiwan' in allowlist['regions']
    
    def test_determine_region(self, temp_dir):
        """Test region determination from country."""
        agent = RegistryAgent(data_dir=temp_dir)
        
        # Test China
        region = agent._determine_region('China', {'regions': {}})
        assert region == 'china'
        
        # Test Taiwan
        region = agent._determine_region('Taiwan', {'regions': {}})
        assert region == 'taiwan'
        
        # Test unknown country
        region = agent._determine_region('Unknown Country', {'regions': {}})
        assert region == 'global'
    
    def test_generate_node_id(self, temp_dir):
        """Test node ID generation."""
        agent = RegistryAgent(data_dir=temp_dir)
        
        node_id = agent._generate_node_id(
            'Test Supplier', 'China', 'Shanghai', 31.2304, 121.4737
        )
        
        assert 'China' in node_id
        assert 'Shanghai' in node_id
        assert 'Test-Supplier' in node_id
        assert '31.23' in node_id
        assert '121.47' in node_id
    
    def test_process_supplier(self, temp_dir, sample_allowlist):
        """Test processing a single supplier."""
        agent = RegistryAgent(data_dir=temp_dir)
        
        # Copy sample allowlist
        import shutil
        Path(temp_dir).mkdir(parents=True, exist_ok=True)
        Path(temp_dir / "inputs").mkdir(parents=True, exist_ok=True)
        shutil.copy(sample_allowlist, Path(temp_dir) / "inputs" / "allowlist_regions.yaml")
        
        # Create sample supplier
        supplier = pd.Series({
            'name': 'Test Supplier',
            'country': 'China',
            'city': 'Shanghai',
            'category': 'PCB',
            'site_url': 'https://test.com',
            'alt_url': '',
            'x_handle': '@test',
            'ticker': 'TEST',
            'region': 'china'
        })
        
        allowlist = agent._load_allowlist()
        
        # Mock geocoding to avoid external API calls
        agent.geocoder.geocode_city_country = lambda city, country: (31.2304, 121.4737)
        
        node = agent._process_supplier(supplier, allowlist)
        
        assert node is not None
        assert node['name'] == 'Test Supplier'
        assert node['country'] == 'China'
        assert node['city'] == 'Shanghai'
        assert node['lat'] == 31.2304
        assert node['lon'] == 121.4737
        assert node['tier'] == 1.0
        assert node['region'] == 'china'
        assert 'node_id' in node
    
    def test_run_complete_flow(self, temp_dir, sample_suppliers, sample_allowlist):
        """Test complete registry agent flow."""
        # Set up test environment
        Path(temp_dir / "inputs").mkdir(parents=True, exist_ok=True)
        Path(temp_dir / "outputs").mkdir(parents=True, exist_ok=True)
        
        import shutil
        shutil.copy(sample_suppliers, Path(temp_dir) / "inputs" / "suppliers_seed.csv")
        shutil.copy(sample_allowlist, Path(temp_dir) / "inputs" / "allowlist_regions.yaml")
        
        agent = RegistryAgent(data_dir=temp_dir)
        
        # Mock geocoding to avoid external API calls
        agent.geocoder.geocode_city_country = lambda city, country: (31.2304, 121.4737)
        
        nodes = agent.run()
        
        assert len(nodes) == 2
        assert all('node_id' in node for node in nodes)
        assert all('lat' in node for node in nodes)
        assert all('lon' in node for node in nodes)
        
        # Check that nodes.json was created
        nodes_path = Path(temp_dir) / "outputs" / "nodes.json"
        assert nodes_path.exists()
        
        # Verify JSON content
        saved_nodes = read_json(str(nodes_path))
        assert len(saved_nodes) == 2
