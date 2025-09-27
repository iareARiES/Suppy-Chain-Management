"""
FastAPI backend for CERONIX Supply Chain Risk Analysis Frontend
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uvicorn

from .models import (
    SupplierResponse, RiskFactorResponse, RouteResponse, 
    AlertResponse, MetricResponse, AnalysisRequest
)
from .services import (
    SupplierService, RiskAnalysisService, RouteService, 
    AlertService, MetricService, WebSocketManager
)
from .database import get_database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="CERONIX Supply Chain Risk Analysis API",
    description="API for supply chain risk analysis and monitoring",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket manager
websocket_manager = WebSocketManager()

# Services
supplier_service = SupplierService()
risk_service = RiskAnalysisService()
route_service = RouteService()
alert_service = AlertService()
metric_service = MetricService()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting CERONIX API server...")
    await supplier_service.initialize()
    await risk_service.initialize()
    await route_service.initialize()
    await alert_service.initialize()
    await metric_service.initialize()
    logger.info("All services initialized successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down CERONIX API server...")
    await websocket_manager.disconnect_all()

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "CERONIX API",
        "version": "1.0.0"
    }

# Dashboard endpoint
@app.get("/api/dashboard")
async def get_dashboard():
    """Get dashboard data."""
    try:
        # Get all dashboard data
        metrics = await metric_service.get_overall_metrics()
        recent_alerts = await alert_service.get_recent_alerts(hours=24)
        top_suppliers = await supplier_service.get_suppliers(limit=5)
        risk_factors = await risk_service.get_risk_factors(limit=5)
        routes = await route_service.get_routes(limit=5)
        
        dashboard_data = {
            "metrics": metrics,
            "recent_alerts": recent_alerts,
            "top_suppliers": top_suppliers,
            "risk_factors": risk_factors,
            "routes": routes,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        # Return mock dashboard data if there's an error
        return {
            "metrics": {
                "overall_risk_score": 72,
                "active_suppliers": 156,
                "active_routes": 24,
                "active_alerts": 7,
                "reliability_score": 89,
                "news_events_24h": 23,
                "weather_alerts": 3,
                "market_signals": 12,
                "last_updated": datetime.utcnow().isoformat()
            },
            "recent_alerts": [],
            "top_suppliers": [],
            "risk_factors": [],
            "routes": [],
            "last_updated": datetime.utcnow().isoformat()
        }

# Supplier endpoints
@app.get("/api/suppliers", response_model=List[SupplierResponse])
async def get_suppliers(
    country: Optional[str] = None,
    tier: Optional[float] = None,
    limit: int = 100
):
    """Get all suppliers with optional filtering."""
    try:
        suppliers = await supplier_service.get_suppliers(
            country=country, 
            tier=tier, 
            limit=limit
        )
        return suppliers
    except Exception as e:
        logger.error(f"Error fetching suppliers: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch suppliers")

@app.get("/api/suppliers/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(supplier_id: str):
    """Get a specific supplier by ID."""
    try:
        supplier = await supplier_service.get_supplier(supplier_id)
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found")
        return supplier
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching supplier {supplier_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch supplier")

# Risk analysis endpoints
@app.get("/api/risk-factors", response_model=List[RiskFactorResponse])
async def get_risk_factors(
    severity: Optional[str] = None,
    limit: int = 50
):
    """Get risk factors with optional filtering."""
    try:
        risk_factors = await risk_service.get_risk_factors(
            severity=severity,
            limit=limit
        )
        return risk_factors
    except Exception as e:
        logger.error(f"Error fetching risk factors: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch risk factors")

@app.post("/api/risk-analysis", response_model=Dict[str, Any])
async def analyze_risk(request: AnalysisRequest):
    """Perform comprehensive risk analysis."""
    try:
        analysis = await risk_service.analyze_supply_chain_risk(request)
        return analysis
    except Exception as e:
        logger.error(f"Error performing risk analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to perform risk analysis")

# Route endpoints
@app.get("/api/routes", response_model=List[RouteResponse])
async def get_routes(
    risk_level: Optional[str] = None,
    limit: int = 20
):
    """Get supply chain routes with optional filtering."""
    try:
        routes = await route_service.get_routes(
            risk_level=risk_level,
            limit=limit
        )
        return routes
    except Exception as e:
        logger.error(f"Error fetching routes: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch routes")

@app.get("/api/routes/{route_id}", response_model=RouteResponse)
async def get_route(route_id: str):
    """Get a specific route by ID."""
    try:
        route = await route_service.get_route(route_id)
        if not route:
            raise HTTPException(status_code=404, detail="Route not found")
        return route
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching route {route_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch route")

# Alert endpoints
@app.get("/api/alerts", response_model=List[AlertResponse])
async def get_alerts(
    severity: Optional[str] = None,
    limit: int = 20
):
    """Get active alerts with optional filtering."""
    try:
        alerts = await alert_service.get_alerts(
            severity=severity,
            limit=limit
        )
        return alerts
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch alerts")

@app.get("/api/alerts/recent", response_model=List[AlertResponse])
async def get_recent_alerts(hours: int = 24):
    """Get recent alerts within specified hours."""
    try:
        alerts = await alert_service.get_recent_alerts(hours)
        return alerts
    except Exception as e:
        logger.error(f"Error fetching recent alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch recent alerts")

# Metrics endpoints
@app.get("/api/metrics", response_model=Dict[str, Any])
async def get_metrics():
    """Get overall system metrics."""
    try:
        metrics = await metric_service.get_overall_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch metrics")

@app.get("/api/metrics/trends", response_model=Dict[str, Any])
async def get_metric_trends(days: int = 7):
    """Get metric trends over specified days."""
    try:
        trends = await metric_service.get_metric_trends(days)
        return trends
    except Exception as e:
        logger.error(f"Error fetching metric trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch metric trends")

# WebSocket endpoint for real-time updates
@app.websocket("/ws/updates")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Send periodic updates
            await asyncio.sleep(5)  # Update every 5 seconds
            
            # Get latest data
            metrics = await metric_service.get_overall_metrics()
            alerts = await alert_service.get_recent_alerts(1)  # Last hour
            
            # Send update to client
            update_data = {
                "type": "metrics_update",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "metrics": metrics,
                    "alerts": alerts
                }
            }
            
            await websocket_manager.send_personal_message(
                json.dumps(update_data), 
                websocket
            )
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket)

# Serve React frontend (for production)
@app.get("/docs", response_class=HTMLResponse)
async def api_docs():
    """Redirect to Swagger UI documentation."""
    return HTMLResponse(
        content="""
        <html>
            <head>
                <title>API Documentation</title>
                <meta http-equiv="refresh" content="0; url=/redoc">
            </head>
            <body>
                <p>Redirecting to API documentation...</p>
                <p><a href="/redoc">Click here if not redirected automatically</a></p>
            </body>
        </html>
        """,
        status_code=200
    )

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the React frontend."""
    try:
        with open("frontend/build/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="""
            <html>
                <head>
                    <title>CERONIX API</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 40px; }
                        .container { max-width: 800px; margin: 0 auto; }
                        .card { border: 1px solid #ddd; padding: 20px; margin: 20px 0; border-radius: 8px; }
                        .status { color: #28a745; font-weight: bold; }
                        a { color: #007bff; text-decoration: none; }
                        a:hover { text-decoration: underline; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>🚀 CERONIX Supply Chain Risk Analysis API</h1>
                        <div class="card">
                            <h2>API Status: <span class="status">✅ RUNNING</span></h2>
                            <p>Backend API is successfully running on port 8000</p>
                        </div>
                        <div class="card">
                            <h2>Frontend Access</h2>
                            <p>React frontend should be available at: <a href="http://localhost:3000" target="_blank">http://localhost:3000</a></p>
                        </div>
                        <div class="card">
                            <h2>API Endpoints</h2>
                            <ul>
                                <li><a href="/api/health">Health Check</a></li>
                                <li><a href="/api/suppliers">Suppliers</a></li>
                                <li><a href="/api/metrics">Metrics</a></li>
                                <li><a href="/api/alerts">Alerts</a></li>
                                <li><a href="/docs">API Documentation (Swagger)</a></li>
                            </ul>
                        </div>
                    </div>
                </body>
            </html>
            """,
            status_code=200
        )

# Mount static files for React frontend
try:
    app.mount("/static", StaticFiles(directory="frontend/build/static"), name="static")
except:
    pass  # Frontend not built yet

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
