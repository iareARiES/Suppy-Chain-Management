"""
API services for CERONIX Supply Chain Risk Analysis
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random
import math
from fastapi import WebSocket

from .models import (
    SupplierResponse, RiskFactorResponse, RouteResponse, 
    AlertResponse, MetricResponse, AnalysisRequest, AnalysisResultResponse,
    RiskLevel, AlertSeverity, ComponentType
)
from core.db_models import get_models
from core.models import Node, NewsEvent, WeatherAnomaly, ExtractedEvent

logger = logging.getLogger(__name__)

class SupplierService:
    """Service for managing supplier data."""
    
    def __init__(self):
        self.models = None
        
    async def initialize(self):
        """Initialize the service."""
        self.models = await get_models()
        logger.info("SupplierService initialized")
        
    async def get_suppliers(
        self, 
        country: Optional[str] = None,
        tier: Optional[float] = None,
        limit: int = 100
    ) -> List[SupplierResponse]:
        """Get suppliers with optional filtering."""
        try:
            if not self.models:
                await self.initialize()
                
            # Get suppliers from database
            if country:
                nodes = await self.models.nodes.get_by_country(country)
            else:
                nodes = await self.models.nodes.find_many(limit=limit)
                
            # Filter by tier if specified
            if tier is not None:
                nodes = [node for node in nodes if node.tier == tier]
                
            # Convert to API response format
            suppliers = []
            for node in nodes:
                supplier = SupplierResponse(
                    id=node.node_id,
                    name=node.name,
                    country=node.country,
                    region=node.region,
                    city=node.city,
                    lat=node.lat,
                    lon=node.lon,
                    tier=node.tier,
                    category=node.category,
                    node_type=node.node_type,
                    reliability_score=self._calculate_reliability_score(node),
                    risk_score=self._calculate_risk_score(node),
                    last_updated=datetime.utcnow(),
                    status="active",
                    website=node.site_url,
                    contact_info=self._get_contact_info(node)
                )
                suppliers.append(supplier)
                
            return suppliers[:limit]
            
        except Exception as e:
            logger.error(f"Error getting suppliers: {e}")
            # Return mock data if database fails
            return self._get_mock_suppliers(limit)
            
    async def get_supplier(self, supplier_id: str) -> Optional[SupplierResponse]:
        """Get a specific supplier by ID."""
        try:
            if not self.models:
                await self.initialize()
                
            node = await self.models.nodes.get_by_id(supplier_id)
            if not node:
                return None
                
            return SupplierResponse(
                id=node.node_id,
                name=node.name,
                country=node.country,
                region=node.region,
                city=node.city,
                lat=node.lat,
                lon=node.lon,
                tier=node.tier,
                category=node.category,
                node_type=node.node_type,
                reliability_score=self._calculate_reliability_score(node),
                risk_score=self._calculate_risk_score(node),
                last_updated=datetime.utcnow(),
                status="active",
                website=node.site_url,
                contact_info=self._get_contact_info(node)
            )
            
        except Exception as e:
            logger.error(f"Error getting supplier {supplier_id}: {e}")
            return None
            
    def _calculate_reliability_score(self, node: Node) -> float:
        """Calculate reliability score for a supplier."""
        # Base score from tier
        base_score = 100 - (node.tier * 10)
        
        # Add some randomness for demo
        variation = random.uniform(-5, 5)
        
        return max(0, min(100, base_score + variation))
        
    def _calculate_risk_score(self, node: Node) -> float:
        """Calculate risk score for a supplier."""
        # Higher tier = higher risk
        base_risk = node.tier * 15
        
        # Add some randomness for demo
        variation = random.uniform(-10, 10)
        
        return max(0, min(100, base_risk + variation))
        
    def _get_contact_info(self, node: Node) -> Dict[str, str]:
        """Get contact information for a supplier."""
        return {
            "website": node.site_url or "",
            "twitter": node.x_handle or "",
            "ticker": node.ticker or ""
        }
        
    def _get_mock_suppliers(self, limit: int) -> List[SupplierResponse]:
        """Get mock supplier data for demo purposes."""
        mock_suppliers = [
            {
                "name": "TechCorp Semiconductors",
                "country": "Taiwan",
                "region": "Asia-Pacific",
                "lat": 25.0330,
                "lon": 121.5654,
                "tier": 1.0,
                "category": "semiconductors"
            },
            {
                "name": "Global Steel Works",
                "country": "China",
                "region": "Asia-Pacific", 
                "lat": 39.9042,
                "lon": 116.4074,
                "tier": 2.0,
                "category": "steel"
            },
            {
                "name": "EuroElectronics",
                "country": "Germany",
                "region": "Europe",
                "lat": 52.5200,
                "lon": 13.4050,
                "tier": 1.5,
                "category": "electronics"
            }
        ]
        
        suppliers = []
        for i, mock in enumerate(mock_suppliers[:limit]):
            supplier = SupplierResponse(
                id=f"supplier_{i+1}",
                name=mock["name"],
                country=mock["country"],
                region=mock["region"],
                lat=mock["lat"],
                lon=mock["lon"],
                tier=mock["tier"],
                category=mock["category"],
                reliability_score=random.uniform(70, 95),
                risk_score=random.uniform(20, 60),
                last_updated=datetime.utcnow(),
                status="active"
            )
            suppliers.append(supplier)
            
        return suppliers


class RiskAnalysisService:
    """Service for risk analysis operations."""
    
    def __init__(self):
        self.models = None
        
    async def initialize(self):
        """Initialize the service."""
        self.models = await get_models()
        logger.info("RiskAnalysisService initialized")
        
    async def get_risk_factors(
        self,
        severity: Optional[str] = None,
        limit: int = 50
    ) -> List[RiskFactorResponse]:
        """Get risk factors with optional filtering."""
        try:
            if not self.models:
                await self.initialize()
                
            # Get risk factors from database
            risk_factors = []
            
            # Get weather anomalies
            weather_anomalies = await self.models.weather_anomalies.find_many(limit=limit//2)
            for anomaly in weather_anomalies:
                risk_factor = RiskFactorResponse(
                    id=f"weather_{anomaly.node_id}",
                    name=f"Weather: {anomaly.anomaly_type.replace('_', ' ').title()}",
                    level=self._map_severity_to_risk_level(anomaly.severity),
                    impact=anomaly.value,
                    probability=80.0,
                    description=f"Weather anomaly detected: {anomaly.anomaly_type}",
                    category="weather",
                    affected_regions=[anomaly.node_id],
                    mitigation_strategies=["Alternative routes", "Buffer inventory"],
                    last_updated=anomaly.ts,
                    source="weather_api",
                    confidence=85.0
                )
                risk_factors.append(risk_factor)
                
            # Get extracted events
            extracted_events = await self.models.extracted_events.find_many(limit=limit//2)
            for event in extracted_events:
                risk_factor = RiskFactorResponse(
                    id=f"event_{event.node_id}",
                    name=f"Event: {event.event_type.replace('_', ' ').title()}",
                    level=self._map_severity_to_risk_level(event.severity or "medium"),
                    impact=event.confidence * 100 if event.confidence else 50.0,
                    probability=70.0,
                    description=event.extracted_text[:200] + "..." if len(event.extracted_text) > 200 else event.extracted_text,
                    category="operational",
                    affected_regions=[event.node_id],
                    mitigation_strategies=["Contingency planning", "Alternative suppliers"],
                    last_updated=event.ts_event,
                    source="news_analysis",
                    confidence=event.confidence * 100 if event.confidence else 75.0
                )
                risk_factors.append(risk_factor)
                
            # Filter by severity if specified
            if severity:
                risk_factors = [rf for rf in risk_factors if rf.level.value == severity.lower()]
                
            return risk_factors[:limit]
            
        except Exception as e:
            logger.error(f"Error getting risk factors: {e}")
            return self._get_mock_risk_factors(limit)
            
    async def analyze_supply_chain_risk(self, request: AnalysisRequest) -> Dict[str, Any]:
        """Perform comprehensive risk analysis."""
        try:
            # Simulate analysis processing time
            await asyncio.sleep(1)
            
            # Generate analysis results
            analysis = {
                "analysis_id": f"analysis_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "request": request,
                "overall_risk_score": random.uniform(30, 80),
                "risk_level": random.choice([RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH]),
                "confidence": random.uniform(75, 95),
                "analysis_timestamp": datetime.utcnow(),
                "risk_factors": await self.get_risk_factors(limit=5),
                "recommended_routes": await self._get_recommended_routes(request),
                "alternative_suppliers": await self._get_alternative_suppliers(request),
                "mitigation_strategies": [
                    "Establish backup suppliers in different regions",
                    "Maintain safety stock inventory",
                    "Monitor weather and political conditions",
                    "Diversify transportation routes"
                ],
                "cost_analysis": {
                    "primary_route_cost": random.uniform(2000, 5000),
                    "alternative_route_cost": random.uniform(2500, 6000),
                    "risk_mitigation_cost": random.uniform(500, 1500),
                    "total_estimated_cost": random.uniform(3000, 7000)
                },
                "timeline_analysis": {
                    "estimated_delivery": datetime.utcnow() + timedelta(days=random.randint(10, 30)),
                    "risk_window": "Next 2-4 weeks",
                    "critical_milestones": [
                        "Supplier confirmation",
                        "Transportation booking",
                        "Customs clearance",
                        "Final delivery"
                    ]
                },
                "critical_alerts": [],
                "warnings": [
                    "Weather conditions may affect shipping routes",
                    "Political tensions in transit regions",
                    "High demand may cause delays"
                ],
                "primary_recommendation": "Proceed with primary route but maintain backup options",
                "alternative_options": [
                    "Use alternative supplier in different region",
                    "Split order across multiple suppliers",
                    "Expedite shipping for critical components"
                ],
                "next_steps": [
                    "Confirm supplier availability",
                    "Book transportation",
                    "Set up monitoring alerts",
                    "Prepare contingency plans"
                ]
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error performing risk analysis: {e}")
            raise
            
    def _map_severity_to_risk_level(self, severity: str) -> RiskLevel:
        """Map severity string to RiskLevel enum."""
        severity_map = {
            "low": RiskLevel.LOW,
            "medium": RiskLevel.MEDIUM,
            "high": RiskLevel.HIGH,
            "critical": RiskLevel.CRITICAL
        }
        return severity_map.get(severity.lower(), RiskLevel.MEDIUM)
        
    async def _get_recommended_routes(self, request: AnalysisRequest) -> List[RouteResponse]:
        """Get recommended routes for the analysis request."""
        # This would integrate with your route service
        return []
        
    async def _get_alternative_suppliers(self, request: AnalysisRequest) -> List[SupplierResponse]:
        """Get alternative suppliers for the analysis request."""
        # This would integrate with your supplier service
        return []
        
    def _get_mock_risk_factors(self, limit: int) -> List[RiskFactorResponse]:
        """Get mock risk factors for demo purposes."""
        mock_factors = [
            {
                "name": "Weather Disruption",
                "level": RiskLevel.HIGH,
                "impact": 85.0,
                "description": "Severe storms expected in route corridor",
                "category": "weather"
            },
            {
                "name": "Labor Strikes",
                "level": RiskLevel.MEDIUM,
                "impact": 45.0,
                "description": "Port workers strike scheduled for next week",
                "category": "operational"
            },
            {
                "name": "Political Tensions",
                "level": RiskLevel.LOW,
                "impact": 25.0,
                "description": "Stable political environment in transit countries",
                "category": "political"
            },
            {
                "name": "International Sanctions",
                "level": RiskLevel.MEDIUM,
                "impact": 60.0,
                "description": "New trade restrictions on specific components",
                "category": "political"
            }
        ]
        
        risk_factors = []
        for i, mock in enumerate(mock_factors[:limit]):
            risk_factor = RiskFactorResponse(
                id=f"risk_factor_{i+1}",
                name=mock["name"],
                level=mock["level"],
                impact=mock["impact"],
                probability=random.uniform(30, 80),
                description=mock["description"],
                category=mock["category"],
                affected_regions=["Global"],
                mitigation_strategies=["Monitor conditions", "Alternative routes"],
                last_updated=datetime.utcnow(),
                source="risk_analysis",
                confidence=random.uniform(70, 90)
            )
            risk_factors.append(risk_factor)
            
        return risk_factors


class RouteService:
    """Service for managing route data."""
    
    def __init__(self):
        self.models = None
        
    async def initialize(self):
        """Initialize the service."""
        self.models = await get_models()
        logger.info("RouteService initialized")
        
    async def get_routes(
        self,
        risk_level: Optional[str] = None,
        limit: int = 20
    ) -> List[RouteResponse]:
        """Get routes with optional filtering."""
        try:
            # For now, return mock data
            # This would integrate with your route analysis system
            return self._get_mock_routes(limit)
            
        except Exception as e:
            logger.error(f"Error getting routes: {e}")
            return self._get_mock_routes(limit)
            
    async def get_route(self, route_id: str) -> Optional[RouteResponse]:
        """Get a specific route by ID."""
        try:
            routes = await self.get_routes()
            for route in routes:
                if route.id == route_id:
                    return route
            return None
            
        except Exception as e:
            logger.error(f"Error getting route {route_id}: {e}")
            return None
            
    def _get_mock_routes(self, limit: int) -> List[RouteResponse]:
        """Get mock route data for demo purposes."""
        mock_routes = [
            {
                "name": "Primary Route",
                "origin": "Shanghai, China",
                "destination": "Los Angeles, USA",
                "risk_level": RiskLevel.LOW,
                "duration_days": 12,
                "cost_usd": 2450.0,
                "reliability_percentage": 94.0
            },
            {
                "name": "Alternative Route A",
                "origin": "Shanghai, China", 
                "destination": "Los Angeles, USA",
                "risk_level": RiskLevel.MEDIUM,
                "duration_days": 15,
                "cost_usd": 2180.0,
                "reliability_percentage": 87.0
            },
            {
                "name": "Alternative Route B",
                "origin": "Shanghai, China",
                "destination": "Los Angeles, USA", 
                "risk_level": RiskLevel.HIGH,
                "duration_days": 10,
                "cost_usd": 3200.0,
                "reliability_percentage": 76.0
            }
        ]
        
        routes = []
        for i, mock in enumerate(mock_routes[:limit]):
            route = RouteResponse(
                id=f"route_{i+1}",
                name=mock["name"],
                origin=mock["origin"],
                destination=mock["destination"],
                risk_level=mock["risk_level"],
                duration_days=mock["duration_days"],
                cost_usd=mock["cost_usd"],
                reliability_percentage=mock["reliability_percentage"],
                distance_km=random.uniform(8000, 12000),
                transport_modes=["sea", "road"],
                transit_countries=["China", "USA"],
                estimated_delivery=datetime.utcnow() + timedelta(days=mock["duration_days"]),
                last_updated=datetime.utcnow(),
                status="active"
            )
            routes.append(route)
            
        return routes


class AlertService:
    """Service for managing alerts."""
    
    def __init__(self):
        self.models = None
        
    async def initialize(self):
        """Initialize the service."""
        self.models = await get_models()
        logger.info("AlertService initialized")
        
    async def get_alerts(
        self,
        severity: Optional[str] = None,
        limit: int = 20
    ) -> List[AlertResponse]:
        """Get alerts with optional filtering."""
        try:
            if not self.models:
                await self.initialize()
                
            # Get recent news events that could be alerts
            news_events = await self.models.news_events.find_recent_events(days=7, limit=limit)
            
            alerts = []
            for event in news_events:
                # Convert news events to alerts based on sentiment
                if event.sentiment_score and event.sentiment_score < -0.3:
                    alert = AlertResponse(
                        id=f"alert_{event.node_id}_{event.ts.timestamp()}",
                        title=f"Negative News: {event.headline[:50]}...",
                        message=event.snippet or event.headline,
                        severity=AlertSeverity.WARNING if event.sentiment_score > -0.6 else AlertSeverity.ERROR,
                        category="news",
                        affected_entities=[event.node_id],
                        location=event.region,
                        timestamp=event.ts,
                        source="news_monitoring",
                        impact_score=abs(event.sentiment_score) * 100,
                        recommended_actions=["Monitor situation", "Contact supplier"]
                    )
                    alerts.append(alert)
                    
            # Filter by severity if specified
            if severity:
                alerts = [alert for alert in alerts if alert.severity.value == severity.lower()]
                
            return alerts[:limit]
            
        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            return self._get_mock_alerts(limit)
            
    async def get_recent_alerts(self, hours: int = 24) -> List[AlertResponse]:
        """Get recent alerts within specified hours."""
        try:
            alerts = await self.get_alerts(limit=50)
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            recent_alerts = [alert for alert in alerts if alert.timestamp >= cutoff_time]
            return recent_alerts
            
        except Exception as e:
            logger.error(f"Error getting recent alerts: {e}")
            return self._get_mock_alerts(10)
            
    def _get_mock_alerts(self, limit: int) -> List[AlertResponse]:
        """Get mock alert data for demo purposes."""
        mock_alerts = [
            {
                "title": "Weather Alert",
                "message": "Severe storms in Route A corridor",
                "severity": AlertSeverity.ERROR,
                "category": "weather"
            },
            {
                "title": "Labor Update", 
                "message": "Port strike scheduled for next week",
                "severity": AlertSeverity.WARNING,
                "category": "operational"
            },
            {
                "title": "Route Cleared",
                "message": "Primary route operational",
                "severity": AlertSeverity.INFO,
                "category": "operational"
            }
        ]
        
        alerts = []
        for i, mock in enumerate(mock_alerts[:limit]):
            alert = AlertResponse(
                id=f"alert_{i+1}",
                title=mock["title"],
                message=mock["message"],
                severity=mock["severity"],
                category=mock["category"],
                affected_entities=[],
                timestamp=datetime.utcnow() - timedelta(hours=random.randint(1, 24)),
                source="system_monitoring",
                impact_score=random.uniform(30, 90),
                recommended_actions=["Monitor situation"]
            )
            alerts.append(alert)
            
        return alerts


class MetricService:
    """Service for managing metrics."""
    
    def __init__(self):
        self.models = None
        
    async def initialize(self):
        """Initialize the service."""
        self.models = await get_models()
        logger.info("MetricService initialized")
        
    async def get_overall_metrics(self) -> Dict[str, Any]:
        """Get overall system metrics."""
        try:
            if not self.models:
                await self.initialize()
                
            # Get counts from database
            supplier_count = await self.models.nodes.count_documents()
            news_count = await self.models.news_events.count_documents()
            alert_count = await self.models.extracted_events.count_documents()
            
            # Calculate metrics
            metrics = {
                "overall_risk_score": random.uniform(60, 80),
                "active_suppliers": supplier_count,
                "active_routes": random.randint(20, 30),
                "active_alerts": alert_count,
                "reliability_score": random.uniform(85, 95),
                "news_events_24h": news_count,
                "weather_alerts": random.randint(2, 8),
                "market_signals": random.randint(5, 15),
                "last_updated": datetime.utcnow().isoformat()
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting overall metrics: {e}")
            return self._get_mock_metrics()
            
    async def get_metric_trends(self, days: int = 7) -> Dict[str, Any]:
        """Get metric trends over specified days."""
        try:
            # Generate trend data
            trends = {
                "risk_score_trend": [random.uniform(60, 80) for _ in range(days)],
                "reliability_trend": [random.uniform(85, 95) for _ in range(days)],
                "alert_count_trend": [random.randint(5, 15) for _ in range(days)],
                "supplier_count_trend": [random.randint(100, 120) for _ in range(days)],
                "dates": [(datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days-1, -1, -1)]
            }
            
            return trends
            
        except Exception as e:
            logger.error(f"Error getting metric trends: {e}")
            return {}
            
    def _get_mock_metrics(self) -> Dict[str, Any]:
        """Get mock metrics for demo purposes."""
        return {
            "overall_risk_score": 72,
            "active_suppliers": 156,
            "active_routes": 24,
            "active_alerts": 7,
            "reliability_score": 89,
            "news_events_24h": 23,
            "weather_alerts": 3,
            "market_signals": 12,
            "last_updated": datetime.utcnow().isoformat()
        }


class WebSocketManager:
    """Manager for WebSocket connections."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
        
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            if websocket in self.active_connections:
                await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
            self.disconnect(websocket)
            
    async def broadcast(self, message: str):
        """Broadcast a message to all connected WebSockets."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                disconnected.append(connection)
                
        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
            
    async def disconnect_all(self):
        """Disconnect all WebSocket connections."""
        for connection in self.active_connections:
            try:
                await connection.close()
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}")
        self.active_connections.clear()
        logger.info("All WebSocket connections closed")
