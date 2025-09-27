# CERONIX Supply Chain Risk Analysis System

A comprehensive, production-ready system that combines multi-agent data collection, real-time risk analysis, and interactive web dashboard for supply chain risk monitoring and prediction.

## 🚀 Features

- **Multi-Agent Architecture**: 8 specialized agents for different data collection and processing tasks
- **Real-time Data Collection**: RSS feeds, SERP API, social media, weather, and market data
- **Deep Content Extraction**: crawl4ai for HTML/PDF processing and event extraction
- **Geographic Intelligence**: Google Maps integration with geocoding and location-based risk assessment
- **Interactive Web Dashboard**: React-based frontend with real-time updates
- **RESTful API**: FastAPI backend with comprehensive endpoints
- **ML-Ready Features**: Structured feature engineering for supply chain risk prediction
- **Production Orchestration**: Prefect-based workflow management
- **Docker Support**: Containerized deployment with docker-compose
- **MongoDB Integration**: Scalable data storage and retrieval

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
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Agent 6       │    │   Agent 7       │    │   Web Dashboard │
│   Features      │    │   Export        │    │   & API         │
│   Builder       │    │   CSV           │    │   (React/FastAPI)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   MongoDB       │
                    │   Database      │
                    └─────────────────┘
```

## 🏗️ System Components

### Agents

1. **Agent 0 - Registry**: Builds canonical supplier registry with Google Maps geocoding
2. **Agent 1 - Social**: Fetches X/Twitter posts for suppliers and news outlets
3. **Agent 2 - News**: Collects news from RSS feeds and SERP API
4. **Agent 3 - Crawl**: Deep crawls URLs and extracts structured events
5. **Agent 4 - Weather**: Detects weather anomalies for each location
6. **Agent 5 - Features**: Builds ML features from all data sources
7. **Agent 6 - Export**: Validates and exports final CSV for ML pipeline
8. **Agent 7 - Export**: Additional export and reporting capabilities

### Core Utilities

- **Models**: Pydantic models for data validation
- **Geo**: Google Maps geocoding and geographic utilities
- **Google Maps Geocoder**: Advanced location services integration
- **NLP**: Sentiment analysis and event classification
- **News**: RSS and SERP API integration
- **IO**: Data persistence utilities
- **Utils**: General utility functions
- **Rate**: Rate limiting and retry logic
- **Database**: MongoDB integration and utilities
- **Schemas**: Database schemas and validation

## 📊 Data Flow

```
Seed Suppliers → Registry → Geocoded Nodes (Google Maps)
     ↓
News/Social/Weather/Crawl → Feature Engineering → MongoDB Storage
     ↓
Web Dashboard ← REST API ← Risk Analysis ← ML-Ready CSV
     ↓
Real-time Monitoring & Alerts
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
SERP_API_KEY=your_serp_api_key
WEATHER_API_KEY=your_weather_api_key
GOOGLE_MAPS_API_KEY=your_google_maps_api_key

# Optional (for enhanced features)
TWITTER_BEARER_TOKEN=your_twitter_token
OPENCAGE_KEY=your_opencage_key

# Database Configuration
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DATABASE=Ceronix
MONGODB_USERNAME=your_username
MONGODB_PASSWORD=your_password
```

### 3. Start the System

```bash
# Start backend API server
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Start frontend (in another terminal)
cd frontend && npm start

# Or use the integrated startup script
python start_servers.py
```

### 4. Access the System

```bash
# Backend API
http://localhost:8000
http://localhost:8000/docs  # API Documentation

# Frontend Dashboard
http://localhost:3000

# Run complete pipeline
python run_complete_pipeline.py
```

### 5. Check Results

```bash
# View generated features
cat data/outputs/features_today.csv

# Check API health
curl http://localhost:8000/api/health

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
│   ├── agent4_crawl.py
│   ├── agent5_weather.py
│   ├── agent6_features.py
│   └── agent7_export.py
├── api/                    # FastAPI backend
│   ├── main.py            # API server
│   ├── services.py        # Business logic
│   ├── models.py          # API models
│   └── database.py        # Database connection
├── frontend/               # React frontend
│   ├── src/
│   │   ├── App.js         # Main app component
│   │   ├── hooks/         # Custom React hooks
│   │   └── services/      # API services
│   ├── package.json       # Frontend dependencies
│   └── Dockerfile         # Frontend container
├── core/                   # Core utilities
│   ├── models.py
│   ├── geo.py
│   ├── google_maps_geocoder.py
│   ├── nlp.py
│   ├── news.py
│   ├── io.py
│   ├── utils.py
│   ├── rate.py
│   ├── db_models.py
│   ├── schemas.py
│   └── db_utils.py
├── orchestrator/           # Workflow orchestration
│   ├── flow_daily.py
│   └── cli.py
├── config/                 # Configuration
│   ├── settings.yaml
│   ├── mongodb.yaml
│   └── mongodb-init.js
├── data/                   # Data storage
│   ├── inputs/            # Seed data
│   └── outputs/           # Generated data
├── cache/                  # Caching
├── logs/                   # Log files
├── tests/                  # Test suite
├── requirements.txt        # Dependencies
├── start_servers.py       # Integrated startup script
├── setup_system.py        # System setup script
├── test_system.py         # System testing script
├── Makefile               # Build commands
├── Dockerfile             # Container setup
└── docker-compose.yaml    # Multi-service setup
```

## 🌐 Web Dashboard & API

### Backend API Endpoints

The system provides a comprehensive REST API:

```bash
# Health Check
GET /api/health

# Dashboard Data
GET /api/dashboard

# Suppliers
GET /api/suppliers
GET /api/suppliers/{id}

# Risk Analysis
GET /api/risk-factors
POST /api/risk-analysis

# Routes
GET /api/routes
GET /api/routes/{id}

# Alerts
GET /api/alerts
GET /api/alerts/recent

# Metrics
GET /api/metrics
GET /api/metrics/trends

# WebSocket for real-time updates
WS /ws/updates
```

### Frontend Features

- **Real-time Dashboard**: Live updates of risk metrics and alerts
- **Supplier Management**: View and manage supplier information
- **Risk Monitoring**: Track risk factors and trends
- **Interactive Maps**: Geographic visualization with Google Maps
- **Alert System**: Real-time notifications for critical events
- **Data Export**: Download reports and analysis results

### API Documentation

Access the interactive API documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

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
# Required API Keys
SERP_API_KEY=your_serp_api_key
WEATHER_API_KEY=your_weather_api_key
GOOGLE_MAPS_API_KEY=your_google_maps_api_key

# Optional API Keys
TWITTER_BEARER_TOKEN=your_twitter_token
OPENCAGE_KEY=your_opencage_key

# Database Configuration
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DATABASE=Ceronix
MONGODB_USERNAME=your_username
MONGODB_PASSWORD=your_password

# System Configuration
HTTP_PROXY=your_proxy_url
LOG_LEVEL=INFO
REACT_APP_API_URL=http://localhost:8000
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

# Test system health
python test_system.py
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

## 🔮 Future Enhancements

- [ ] Real-time streaming data ingestion
- [ ] Advanced NLP models for event classification
- [ ] Graph-based risk propagation modeling
- [ ] Multi-language support for global suppliers
- [ ] Integration with more data sources
- [ ] Advanced caching and performance optimization
- [ ] Machine learning model integration
- [ ] Advanced analytics and reporting
- [ ] Mobile application support
- [ ] Multi-tenant architecture

## 🎯 System Status

### Current Capabilities
- ✅ **Backend API**: Fully functional with all endpoints
- ✅ **Frontend Dashboard**: React-based with real-time updates
- ✅ **Multi-Agent System**: All 8 agents implemented and working
- ✅ **Google Maps Integration**: Advanced geocoding and location services
- ✅ **MongoDB Integration**: Scalable data storage
- ✅ **Docker Support**: Containerized deployment ready
- ✅ **Error Handling**: Robust error handling and logging
- ✅ **Performance Optimized**: Debounced API calls and efficient rendering

### Production Ready Features
- 🔒 **Security**: Environment variable management and API key protection
- 📊 **Monitoring**: Comprehensive logging and health checks
- 🚀 **Scalability**: Docker containerization and MongoDB integration
- 🔄 **Real-time**: WebSocket support for live updates
- 📱 **Responsive**: Modern React frontend with optimized performance

## 📞 Support & Contact

For technical support, issues, or questions:

1. **Check System Health**: `python test_system.py`
2. **View Logs**: `tail -f logs/supply_agents.log`
3. **API Documentation**: http://localhost:8000/docs
4. **Health Check**: http://localhost:8000/api/health

## 📄 License

This project is part of the CERONIX Supply Chain Risk Analysis System. All rights reserved.

---

**Built with ❤️ for supply chain risk management**
