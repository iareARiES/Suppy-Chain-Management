# CERONIX Database Setup Guide

This guide explains how to set up and use MongoDB with the CERONIX supply chain risk analysis system.

## Prerequisites

1. **MongoDB Server**: Install MongoDB locally or use MongoDB Atlas
2. **Python Dependencies**: Install the required packages

## Installation

### 1. Install MongoDB Dependencies

```bash
pip install motor pymongo dnspython
```

### 2. MongoDB Server Setup

#### Option A: Local MongoDB Installation

**Windows:**
```bash
# Download and install MongoDB Community Server from:
# https://www.mongodb.com/try/download/community

# Start MongoDB service
net start MongoDB
```

**macOS:**
```bash
# Install using Homebrew
brew tap mongodb/brew
brew install mongodb-community

# Start MongoDB
brew services start mongodb/brew/mongodb-community
```

**Linux (Ubuntu/Debian):**
```bash
# Import MongoDB public key
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -

# Add MongoDB repository
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list

# Install MongoDB
sudo apt-get update
sudo apt-get install -y mongodb-org

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod
```

#### Option B: MongoDB Atlas (Cloud)

1. Create a free account at [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Create a new cluster
3. Get your connection string
4. Update the environment variables (see Configuration section)

### 3. Environment Configuration

Copy the example environment file and update the MongoDB settings:

```bash
cp env.example .env
```

Edit `.env` and configure MongoDB settings:

```env
# MongoDB Configuration
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DATABASE=Ceronix
MONGODB_USERNAME=your_username  # Optional
MONGODB_PASSWORD=your_password  # Optional
MONGODB_AUTH_SOURCE=admin
MONGODB_CONNECTION_TIMEOUT=5000
MONGODB_SERVER_SELECTION_TIMEOUT=5000
```

For MongoDB Atlas, use the connection string format:
```env
MONGODB_CONNECTION_STRING=mongodb+srv://username:password@cluster.mongodb.net/Ceronix?retryWrites=true&w=majority
```

## Database Initialization

### 1. Initialize Database

```bash
# Initialize database with indexes
python -m core.init_database init

# Or using the CLI
python -m orchestrator.db_cli init
```

### 2. Seed Initial Data

```bash
# Seed database with initial data from CSV and YAML files
python -m core.init_database seed

# Or using the CLI
python -m orchestrator.db_cli seed
```

### 3. Test Database Connection

```bash
# Run database tests
python test_database.py
```

## Database CLI Commands

The system includes a comprehensive CLI for database management:

```bash
# Check database health
python -m orchestrator.db_cli health

# Initialize database
python -m orchestrator.db_cli init

# Seed initial data
python -m orchestrator.db_cli seed

# Show database statistics
python -m orchestrator.db_cli stats

# List all collections
python -m orchestrator.db_cli collections

# Clean up old data (keep last 30 days)
python -m orchestrator.db_cli cleanup --days 30

# Create backup of all collections
python -m orchestrator.db_cli backup

# Create backup of specific collection
python -m orchestrator.db_cli backup --collection nodes

# Migrate CSV to MongoDB
python -m orchestrator.db_cli migrate-csv data/inputs/suppliers_seed.csv nodes

# Export collection to CSV
python -m orchestrator.db_cli export-csv nodes data/outputs/nodes_export.csv

# Reset database (WARNING: Deletes all data)
python -m orchestrator.db_cli reset
```

## Database Schema

The system uses the following collections:

### 1. **nodes**
- Supply chain nodes (suppliers, manufacturers, etc.)
- Indexes: node_id (unique), country, node_type, tier, coordinates

### 2. **news_events**
- News articles and events related to supply chain nodes
- Indexes: node_id, timestamp, outlet, sentiment_score, URL (unique)

### 3. **social_events**
- Social media posts and events
- Indexes: node_id, timestamp, handle, sentiment_score, engagement_count

### 4. **extracted_events**
- Events extracted from deep crawling (fires, strikes, etc.)
- Indexes: node_id, event_type, timestamp, severity, confidence

### 5. **weather_anomalies**
- Weather anomalies affecting supply chain nodes
- Indexes: node_id, timestamp, anomaly_type, severity

### 6. **market_signals**
- Market signals and financial data
- Indexes: node_id, ticker, timestamp, signal_type

### 7. **feature_rows**
- ML feature vectors for risk analysis
- Indexes: node_id (unique), country, node_type, tier

### 8. **region_configs**
- Regional configuration data
- Indexes: name (unique)

## Usage Examples

### Python Code Examples

```python
import asyncio
from core.db_models import get_models
from core.models import Node, NewsEvent

async def example_usage():
    # Get database models
    models = await get_models()
    
    # Create a new node
    node = Node.from_raw(
        name="Example Supplier",
        country="USA",
        lat=40.7128,
        lon=-74.0060
    )
    node_id = await models.nodes.create(node)
    
    # Create a news event
    news = NewsEvent(
        node_id=node.node_id,
        url="https://example.com/news",
        headline="Example News",
        outlet="Example News",
        ts=datetime.utcnow()
    )
    news_id = await models.news_events.create(news)
    
    # Query nodes by country
    usa_nodes = await models.nodes.get_by_country("USA")
    
    # Get recent news events
    recent_news = await models.news_events.get_recent(days=7)

# Run the example
asyncio.run(example_usage())
```

## Performance Optimization

### 1. Indexes
The system automatically creates optimized indexes for all collections. Indexes are created for:
- Primary keys (unique)
- Foreign keys (node_id references)
- Timestamp fields (for time-based queries)
- Text search fields
- Geographic coordinates

### 2. Connection Pooling
MongoDB connections are pooled for better performance:
- Max pool size: 100 connections
- Min pool size: 10 connections
- Connection timeout: 5 seconds

### 3. Data Retention
Configure data retention policies in `config/mongodb.yaml`:
- News events: 90 days
- Social events: 90 days
- Extracted events: 180 days
- Weather anomalies: 365 days
- Market signals: 365 days

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Ensure MongoDB is running
   - Check host and port settings
   - Verify firewall settings

2. **Authentication Failed**
   - Check username/password
   - Verify auth source database
   - Ensure user has proper permissions

3. **Index Creation Failed**
   - Check disk space
   - Verify database permissions
   - Review MongoDB logs

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Health Check

```bash
# Check database health
python -m orchestrator.db_cli health

# Get detailed statistics
python -m orchestrator.db_cli stats
```

## Backup and Recovery

### Automated Backups

Configure automated backups in `config/mongodb.yaml`:

```yaml
backup:
  enabled: true
  schedule: "daily"
  retention_days: 30
```

### Manual Backup

```bash
# Create backup of all collections
python -m orchestrator.db_cli backup

# Create backup of specific collection
python -m orchestrator.db_cli backup --collection nodes
```

### Data Export

```bash
# Export collection to CSV
python -m orchestrator.db_cli export-csv nodes data/outputs/nodes_backup.csv
```

## Security Considerations

1. **Authentication**: Enable MongoDB authentication in production
2. **Network Security**: Use VPN or IP whitelisting
3. **Data Encryption**: Enable encryption at rest and in transit
4. **Access Control**: Implement role-based access control
5. **Audit Logging**: Enable MongoDB audit logs

## Monitoring

### Database Metrics

Monitor key metrics:
- Connection count
- Query performance
- Index usage
- Storage usage
- Replication lag (if using replica sets)

### Health Monitoring

```bash
# Regular health checks
python -m orchestrator.db_cli health

# Performance monitoring
python -m orchestrator.db_cli stats
```

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review MongoDB documentation
3. Check system logs
4. Run database tests: `python test_database.py`
