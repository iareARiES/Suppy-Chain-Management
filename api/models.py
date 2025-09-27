"""
API models and schemas for CERONIX Supply Chain Risk Analysis
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ComponentType(str, Enum):
    SEMICONDUCTORS = "semiconductors"
    BATTERIES = "batteries"
    STEEL = "steel"
    ELECTRONICS = "electronics"
    TEXTILES = "textiles"
    CHEMICALS = "chemicals"
    AUTOMOTIVE = "automotive"

# Request Models
class AnalysisRequest(BaseModel):
    """Request model for supply chain risk analysis."""
    component_type: ComponentType
    seller_location: str
    import_location: str
    quantity: Optional[int] = 1
    urgency: Optional[str] = "normal"  # normal, urgent, critical
    budget_constraint: Optional[float] = None
    timeline_days: Optional[int] = None

class SupplierFilter(BaseModel):
    """Filter model for suppliers."""
    country: Optional[str] = None
    tier: Optional[float] = None
    category: Optional[str] = None
    region: Optional[str] = None
    min_reliability: Optional[float] = None

# Response Models
class SupplierResponse(BaseModel):
    """Response model for supplier data."""
    id: str
    name: str
    country: str
    region: Optional[str] = None
    city: Optional[str] = None
    lat: float
    lon: float
    tier: float
    category: Optional[str] = None
    node_type: str = "supplier"
    reliability_score: float = Field(ge=0, le=100)
    risk_score: float = Field(ge=0, le=100)
    last_updated: datetime
    status: str = "active"  # active, inactive, suspended
    website: Optional[str] = None
    contact_info: Optional[Dict[str, str]] = None

class RiskFactorResponse(BaseModel):
    """Response model for risk factors."""
    id: str
    name: str
    level: RiskLevel
    impact: float = Field(ge=0, le=100)
    probability: float = Field(ge=0, le=100)
    description: str
    category: str  # weather, political, economic, operational
    affected_regions: List[str] = []
    mitigation_strategies: List[str] = []
    last_updated: datetime
    source: str
    confidence: float = Field(ge=0, le=100)

class RouteResponse(BaseModel):
    """Response model for supply chain routes."""
    id: str
    name: str
    origin: str
    destination: str
    risk_level: RiskLevel
    duration_days: int
    cost_usd: float
    reliability_percentage: float = Field(ge=0, le=100)
    distance_km: Optional[float] = None
    transport_modes: List[str] = []  # sea, air, road, rail
    transit_countries: List[str] = []
    estimated_delivery: datetime
    last_updated: datetime
    status: str = "active"  # active, suspended, closed
    alternative_routes: List[str] = []

class AlertResponse(BaseModel):
    """Response model for alerts."""
    id: str
    title: str
    message: str
    severity: AlertSeverity
    category: str  # weather, political, operational, security
    affected_entities: List[str] = []  # supplier IDs, route IDs
    location: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None
    timestamp: datetime
    expires_at: Optional[datetime] = None
    acknowledged: bool = False
    source: str
    impact_score: float = Field(ge=0, le=100)
    recommended_actions: List[str] = []

class MetricResponse(BaseModel):
    """Response model for metrics."""
    name: str
    value: float
    unit: str
    trend: str  # up, down, stable
    change_percentage: float
    last_updated: datetime
    target_value: Optional[float] = None
    status: str  # good, warning, critical

class TrackingResponse(BaseModel):
    """Response model for shipment tracking."""
    id: str
    shipment_id: str
    supplier_id: str
    route_id: str
    status: str  # pending, in_transit, delayed, delivered, cancelled
    current_location: str
    progress_percentage: float = Field(ge=0, le=100)
    estimated_delivery: datetime
    actual_delivery: Optional[datetime] = None
    last_update: datetime
    milestones: List[Dict[str, Any]] = []
    delays: List[Dict[str, Any]] = []

class NewsEventResponse(BaseModel):
    """Response model for news events."""
    id: str
    headline: str
    snippet: str
    url: str
    outlet: str
    timestamp: datetime
    sentiment_score: float = Field(ge=-1, le=1)
    relevance_score: float = Field(ge=0, le=100)
    affected_suppliers: List[str] = []
    tags: List[str] = []
    language: str = "en"

class WeatherAnomalyResponse(BaseModel):
    """Response model for weather anomalies."""
    id: str
    type: str  # storm, flood, drought, extreme_heat, extreme_cold
    severity: RiskLevel
    location: str
    coordinates: Dict[str, float]
    affected_radius_km: float
    start_time: datetime
    end_time: Optional[datetime] = None
    intensity: float = Field(ge=0, le=100)
    description: str
    affected_routes: List[str] = []
    affected_suppliers: List[str] = []

class MarketSignalResponse(BaseModel):
    """Response model for market signals."""
    id: str
    ticker: Optional[str] = None
    signal_type: str  # price, volume, volatility, news_sentiment
    value: float
    change_percentage: float
    z_score: Optional[float] = None
    timestamp: datetime
    confidence: float = Field(ge=0, le=100)
    related_suppliers: List[str] = []

class AnalysisResultResponse(BaseModel):
    """Response model for comprehensive risk analysis."""
    analysis_id: str
    request: AnalysisRequest
    overall_risk_score: float = Field(ge=0, le=100)
    risk_level: RiskLevel
    confidence: float = Field(ge=0, le=100)
    analysis_timestamp: datetime
    
    # Detailed results
    risk_factors: List[RiskFactorResponse] = []
    recommended_routes: List[RouteResponse] = []
    alternative_suppliers: List[SupplierResponse] = []
    mitigation_strategies: List[str] = []
    cost_analysis: Dict[str, float] = {}
    timeline_analysis: Dict[str, Any] = {}
    
    # Alerts and warnings
    critical_alerts: List[AlertResponse] = []
    warnings: List[str] = []
    
    # Recommendations
    primary_recommendation: str
    alternative_options: List[str] = []
    next_steps: List[str] = []

class WebSocketMessage(BaseModel):
    """WebSocket message model."""
    type: str  # metrics_update, alert, route_update, supplier_update
    timestamp: datetime
    data: Dict[str, Any]
    source: str = "ceronix_api"

class DashboardDataResponse(BaseModel):
    """Complete dashboard data response."""
    metrics: Dict[str, MetricResponse] = {}
    risk_factors: List[RiskFactorResponse] = []
    routes: List[RouteResponse] = []
    alerts: List[AlertResponse] = []
    suppliers: List[SupplierResponse] = []
    news_events: List[NewsEventResponse] = []
    weather_anomalies: List[WeatherAnomalyResponse] = []
    market_signals: List[MarketSignalResponse] = []
    last_updated: datetime

class SearchRequest(BaseModel):
    """Search request model."""
    query: str
    filters: Optional[Dict[str, Any]] = {}
    limit: int = 20
    offset: int = 0

class SearchResponse(BaseModel):
    """Search response model."""
    results: List[Dict[str, Any]] = []
    total_count: int
    query: str
    filters: Dict[str, Any] = {}
    search_time_ms: float

class ExportRequest(BaseModel):
    """Export request model."""
    data_type: str  # suppliers, routes, risk_factors, alerts
    format: str = "csv"  # csv, json, xlsx
    filters: Optional[Dict[str, Any]] = {}
    include_metadata: bool = True

class ExportResponse(BaseModel):
    """Export response model."""
    download_url: str
    filename: str
    file_size_bytes: int
    expires_at: datetime
    format: str
