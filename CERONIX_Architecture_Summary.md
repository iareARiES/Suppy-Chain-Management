# CERONIX Supply Chain Risk Analysis System - Architecture Summary

## 🎯 **System Overview**
The CERONIX system is a comprehensive, production-ready platform that combines multi-agent data collection, real-time risk analysis, and interactive web dashboard for supply chain risk monitoring and prediction.

## 🏗️ **Architecture Layers**

### 1. **Frontend Layer (React)**
- **Technology**: React 18, JavaScript ES6+, CSS3, WebSocket
- **Components**: Dashboard, Suppliers, Alerts, Risk Monitoring, Interactive Maps
- **Features**: Real-time updates, responsive design, modern UI/UX

### 2. **API Layer (FastAPI)**
- **Technology**: FastAPI, Python 3.11+, Pydantic, Uvicorn
- **Endpoints**: REST API with WebSocket support
- **Features**: Authentication, rate limiting, comprehensive documentation

### 3. **Data Layer (MongoDB)**
- **Technology**: MongoDB 6.0+, Motor (async driver)
- **Collections**: nodes, news_events, extracted_events, weather_anomalies, features, alerts
- **Features**: Scalable storage, geospatial indexing, horizontal scaling

### 4. **Multi-Agent Processing Layer**
- **Agents**: 8 specialized agents for different data collection and processing tasks
- **Orchestration**: Prefect 2.0+ for workflow management
- **Features**: Parallel processing, error handling, retry logic

### 5. **Core Services Layer**
- **Services**: Geo, NLP, News, IO, Utils, Rate Limiting, Database, Schemas
- **Features**: Reusable components, modular design, comprehensive utilities

### 6. **External Data Sources**
- **APIs**: Google Maps, SERP API, Weather API, Twitter API, RSS feeds
- **Tools**: crawl4ai for web scraping
- **Features**: Rate limiting, caching, fallback mechanisms

## 🤖 **Agent Architecture**

| Agent | Purpose | Input | Output | Dependencies |
|-------|---------|-------|--------|--------------|
| **Agent 0** | Registry | Raw supplier CSV | Geocoded nodes | Google Maps API |
| **Agent 1** | Social Media | Supplier names/handles | Social events | Twitter API, NLP |
| **Agent 2** | News | Supplier names/regions | News events | SERP API, RSS feeds |
| **Agent 3** | Crawl | URLs from sources | Structured events | crawl4ai, rate limiting |
| **Agent 4** | Weather | Supplier locations | Weather anomalies | Weather API |
| **Agent 5** | Features | All collected data | ML features | All previous agents |
| **Agent 6** | Export | Feature vectors | CSV files | Agent 5, IO services |
| **Agent 7** | Export | All processed data | Reports/analytics | All agents, MongoDB |

## 📊 **Data Flow**

```
Seed Data → Registry Agent → Geocoded Nodes → Multi-Agent Processing → Feature Engineering → Risk Analysis → Dashboard
     ↓
MongoDB Storage ← API Server ← Real-time Updates ← WebSocket
```

## 🌐 **API Endpoints**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | System health check |
| `/api/dashboard` | GET | Dashboard data aggregation |
| `/api/suppliers` | GET/POST | Supplier management |
| `/api/risk-factors` | GET | Risk analysis data |
| `/api/routes` | GET | Supply chain routes |
| `/api/alerts` | GET | Alert management |
| `/api/metrics` | GET | System metrics |
| `/ws/updates` | WS | Real-time updates |

## 🗄️ **Database Schema**

### Collections:
- **nodes**: Suppliers, locations, metadata
- **news_events**: Articles, sentiment, timestamps
- **extracted_events**: Crawled data, structured events
- **weather_anomalies**: Weather data, anomaly flags
- **features**: ML data, vectors, scores
- **alerts**: Warnings, critical events
- **routes**: Supply routes, logistics data
- **metrics**: System metrics, performance data

## 🚀 **Deployment Architecture**

### Docker Containers:
- **Backend Container**: FastAPI, Python, agents, core services
- **Frontend Container**: React, Node.js, Nginx
- **Database Container**: MongoDB with persistent storage

### Infrastructure:
- **Containerization**: Docker, Docker Compose
- **Web Server**: Nginx for static file serving
- **Monitoring**: Health checks, logging, metrics
- **Security**: Environment variables, API keys, encryption

## 🔧 **Core Services**

| Service | Purpose | Key Features |
|---------|---------|--------------|
| **geo.py** | Geocoding | Google Maps integration, location services |
| **nlp.py** | NLP Processing | Sentiment analysis, event classification |
| **news.py** | News Processing | RSS feeds, SERP API, content analysis |
| **io.py** | I/O Operations | File handling, caching, storage |
| **utils.py** | Utilities | Helper functions, math operations, stats |
| **rate.py** | Rate Limiting | Throttling, retry logic, API limits |
| **db_models.py** | Database | MongoDB models, queries, operations |
| **schemas.py** | Validation | Data validation, schemas, types |

## 🔐 **Security Features**

- **Environment Variables**: API keys and secrets management
- **API Security**: CORS, rate limiting, input validation
- **Data Encryption**: MongoDB encryption, secure connections
- **Infrastructure Security**: Docker security, network isolation

## 📈 **Performance Characteristics**

- **Concurrency**: Async/await throughout
- **Rate Limiting**: Configurable per API
- **Caching**: Multi-level caching strategy
- **Scalability**: Horizontal scaling ready
- **Real-time**: WebSocket for live updates
- **Database**: Optimized queries and indexing

## 🎯 **Key Benefits**

1. **Real-time Risk Monitoring**: Live updates and alerting
2. **Automated Data Collection**: Multi-source data aggregation
3. **Intelligent Processing**: ML-ready feature engineering
4. **Scalable Architecture**: Growth-ready infrastructure
5. **Interactive Visualization**: Modern web dashboard
6. **Production Ready**: Docker deployment with monitoring

## 🔮 **Future Enhancements**

- Machine learning model integration
- Advanced analytics and reporting
- Mobile application support
- Multi-tenant architecture
- Real-time streaming with Apache Kafka
- Advanced security with OAuth 2.0
- Microservices decomposition
- Graph-based risk propagation

## 📞 **Support & Documentation**

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health
- **System Testing**: `python test_system.py`
- **Logs**: `tail -f logs/supply_agents.log`

---

**Built with ❤️ for supply chain risk management**
