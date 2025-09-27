# Multi-Agent Supply Chain Risk Analysis System

A production-ready, multi-agent system that ingests region-scoped supplier/news sources, searches via SERP API, deep-scrapes with crawl4ai, enriches with weather/markets, aggregates features, and exports a train-ready CSV per node for supply chain risk prediction.

## 🚀 Features

- **Multi-Agent Architecture**: 8 specialized agents for different data collection and processing tasks
- **Real-time Data Collection**: RSS feeds, SERP API, social media, weather, and market data
- **Deep Content Extraction**: crawl4ai for HTML/PDF processing and event extraction
- **Geographic Intelligence**: Geocoding and location-based risk assessment
- **ML-Ready Features**: Structured feature engineering for supply chain risk prediction
- **Production Orchestration**: Prefect-based workflow management
- **Docker Support**: Containerized deployment with docker-compose

## 📋 Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Agent 0       │    │   Agent 1       │    │   Agent 2       │
│   Registry      │    │   Social/X      │    │   News          │
│   Normalizer    │    │   Fetcher       │    │   Fetcher       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Agent 3       │    │   Agent 4       │    │   Agent 5       │
│   Deep Crawl    │    │   Weather       │    │   Feature       │
│   Extraction    │    │   Anomalies     │    │   Builder       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Agent 6       │
                    │   Export        │
                    │   CSV           │
                    └─────────────────┘
```

## 🏗️ System Components

### Agents

1. **Agent 0 - Registry**: Builds canonical supplier registry with geocoding
2. **Agent 1 - Social**: Fetches X/Twitter posts for suppliers and news outlets
3. **Agent 2 - News**: Collects news from RSS feeds and SERP API
4. **Agent 3 - Crawl**: Deep crawls URLs and extracts structured events
5. **Agent 4 - Weather**: Detects weather anomalies for each location
6. **Agent 5 - Features**: Builds ML features from all data sources
7. **Agent 6 - Export**: Validates and exports final CSV for ML pipeline

### Core Utilities

- **Models**: Pydantic models for data validation
- **Geo**: Geocoding and geographic utilities
- **NLP**: Sentiment analysis and event classification
- **News**: RSS and SERP API integration
- **IO**: Data persistence utilities
- **Utils**: General utility functions
- **Rate**: Rate limiting and retry logic

## 📊 Data Flow

```
Seed Suppliers → Registry → Geocoded Nodes
     ↓
News/Social/Weather/Crawl → Feature Engineering → ML-Ready CSV
     ↓
Risk Prediction Pipeline (External ML System)
```

## 🚀 Quick Start

### 1. Setup

```bash
# Clone and setup
cd supply-agents
make setup

# Copy environment file and configure
cp env.example .env
# Edit .env with your API keys
```

### 2. Configure API Keys

Edit `.env` file:

```bash
# Required
SERP_API_KEY=U2BP9bUMpLgbTRi1RFraq6hm
WEATHER_API_KEY=12cdd7b6c0a14759939174503251909

# Optional (for enhanced features)
TWITTER_BEARER_TOKEN=your_twitter_token
OPENCAGE_KEY=your_opencage_key
```

### 3. Run Pipeline

```bash
# Run complete pipeline
make run

# Or use CLI directly
python -m orchestrator.cli run-all
```

### 4. Check Results

```bash
# View generated features
cat data/outputs/features_today.csv

# Check logs
tail -f logs/supply_agents.log
```

## 📁 Directory Structure

```
supply-agents/
├── agents/                 # Agent implementations
│   ├── agent0_registry.py
│   ├── agent1_social.py
│   ├── agent2_news.py
│   ├── agent3_market.py
│   ├── agent4_crawl.py
│   ├── agent5_weather.py
│   ├── agent6_features.py
│   └── agent7_export.py
├── core/                   # Core utilities
│   ├── models.py
│   ├── geo.py
│   ├── nlp.py
│   ├── news.py
│   ├── io.py
│   ├── utils.py
│   └── rate.py
├── orchestrator/           # Workflow orchestration
│   ├── flow_daily.py
│   └── cli.py
├── config/                 # Configuration
│   └── settings.yaml
├── data/                   # Data storage
│   ├── inputs/            # Seed data
│   └── outputs/           # Generated data
├── cache/                  # Caching
├── logs/                   # Log files
├── tests/                  # Test suite
├── requirements.txt        # Dependencies
├── Makefile               # Build commands
├── Dockerfile             # Container setup
└── docker-compose.yaml    # Multi-service setup
```

## 🔧 Configuration

### Settings (config/settings.yaml)

```yaml
serp:
  base: "https://serpapi.com/search.json"
  engine: "google"
  results: 10

crawl:
  concurrency: 4
  timeout_s: 20

nlp:
  model: "distilbert-base-uncased-finetuned-sst-2-english"

windows:
  news_1d_hours: 24
  news_7d_days: 7
  neg_frac_3d_hours: 72
  baseline_days: 30

weather:
  provider: "open-meteo"
  precip_heavy_mm: 40
  wind_high_kmh: 70
  heatwave_c: 38
```

### Environment Variables

```bash
# Required
SERP_API_KEY=your_serp_api_key

# Optional
TWITTER_BEARER_TOKEN=your_twitter_token
OPENCAGE_KEY=your_opencage_key
HTTP_PROXY=your_proxy_url
LOG_LEVEL=INFO
```

## 📊 Output Schema

The system generates `data/outputs/features_today.csv` with the following schema:

| Column | Type | Description |
|--------|------|-------------|
| node_id | string | Unique node identifier |
| node_type | string | Type of node (supplier) |
| name | string | Supplier name |
| country | string | Country |
| lat | float | Latitude |
| lon | float | Longitude |
| tier | float | Supplier tier |
| news_count_1d | int | News articles in last 24h |
| news_count_7d | int | News articles in last 7 days |
| neg_tone_frac_3d | float | Negative sentiment fraction (0-1) |
| weather_anomaly_7d | int | Weather anomaly flag (0/1) |
| strike_flag_7d | int | Labor strike flag (0/1) |
| avg_lead_time_days | float | Average lead time (optional) |
| inventory_days | float | Inventory coverage (optional) |
| single_sourced | int | Single-sourced flag (0/1) |
| past_delay_days | int | Past delay days |
| news_velocity | float | News velocity z-score |
| disruption_within_7d | int | Target variable (optional) |
| days_to_disruption | int | Days to disruption (optional) |

## 🧪 Testing

```bash
# Run all tests
make test

# Test individual agents
python -m orchestrator.cli test-agents

# Test specific components
pytest tests/test_registry.py -v
pytest tests/test_features.py -v
```

## 🐳 Docker Deployment

### Build and Run

```bash
# Build image
docker build -t supply-chain-risk-analysis .

# Run container
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  -e SERP_API_KEY=your_key \
  supply-chain-risk-analysis
```

### Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🔄 Workflow Orchestration

### Prefect Integration

```bash
# Start Prefect server
python -m orchestrator.cli serve-flows

# Access Prefect UI
open http://localhost:4200
```

### Scheduled Runs

The system includes Prefect flows for:
- Daily pipeline execution
- Registry-only updates
- Export-only operations

## 📈 Monitoring and Logging

- **Structured Logging**: JSON-formatted logs with timestamps
- **Error Handling**: Graceful degradation with retry logic
- **Rate Limiting**: Respectful API usage with backoff
- **Caching**: Local caching for geocoding and API responses

## 🔧 Development

### Setup Development Environment

```bash
make dev-setup
```

### Code Quality

```bash
# Format code
make format

# Lint code
make lint

# Run full development workflow
make dev
```

### Adding New Agents

1. Create agent file in `agents/`
2. Implement required interface
3. Add to Prefect flow in `orchestrator/flow_daily.py`
4. Add tests in `tests/`
5. Update documentation

## 🤝 Integration with ML Pipeline

The generated CSV is designed to integrate with the risk analysis ML pipeline:

```python
# Load features
import pandas as pd
features_df = pd.read_csv('data/outputs/features_today.csv')

# Use with ML pipeline
from supplychain_ml_pipeline import SupplyChainMLPipeline
pipeline = SupplyChainMLPipeline("supplychain_model.pth")
predictions = pipeline.predict_risk(features_df)
```

## 📝 License

This project is part of the supply chain risk analysis system. See the main repository for license information.

## 🆘 Support

For issues and questions:
1. Check the logs in `logs/supply_agents.log`
2. Run `python -m orchestrator.cli check-setup`
3. Review the configuration files
4. Check API key validity and rate limits

## 🔮 Future Enhancements

- [ ] Real-time streaming data ingestion
- [ ] Advanced NLP models for event classification
- [ ] Graph-based risk propagation modeling
- [ ] Multi-language support for global suppliers
- [ ] Integration with more data sources
- [ ] Advanced caching and performance optimization
#   S u p p y - C h a i n - M a n a g e m e n t  
 