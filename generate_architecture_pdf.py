#!/usr/bin/env python3
"""
Generate comprehensive PDF documentation for CERONIX Supply Chain Risk Analysis System
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import Color, black, blue, red, green, orange
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.platypus import Image as RLImage
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics import renderPDF
import os
from datetime import datetime

def create_architecture_diagram():
    """Create a simple architecture diagram using ReportLab drawing"""
    drawing = Drawing(400, 300)
    
    # Main system box
    drawing.add(Rect(50, 200, 300, 80, fillColor=colors.lightblue, strokeColor=colors.black))
    drawing.add(String(200, 230, "CERONIX SUPPLY CHAIN RISK ANALYSIS", 
                      textAnchor="middle", fontSize=12, fillColor=colors.black))
    
    # Frontend layer
    drawing.add(Rect(60, 160, 80, 30, fillColor=colors.lightgreen, strokeColor=colors.black))
    drawing.add(String(100, 175, "Frontend", textAnchor="middle", fontSize=10))
    
    # API layer
    drawing.add(Rect(150, 160, 80, 30, fillColor=colors.lightyellow, strokeColor=colors.black))
    drawing.add(String(190, 175, "API Layer", textAnchor="middle", fontSize=10))
    
    # Data layer
    drawing.add(Rect(240, 160, 80, 30, fillColor=colors.lightcoral, strokeColor=colors.black))
    drawing.add(String(280, 175, "Data Layer", textAnchor="middle", fontSize=10))
    
    # Agent layer
    drawing.add(Rect(60, 120, 260, 30, fillColor=colors.lightgrey, strokeColor=colors.black))
    drawing.add(String(190, 135, "Multi-Agent Processing Layer", textAnchor="middle", fontSize=10))
    
    # Core services
    drawing.add(Rect(60, 80, 260, 30, fillColor=colors.lightcyan, strokeColor=colors.black))
    drawing.add(String(190, 95, "Core Services Layer", textAnchor="middle", fontSize=10))
    
    # External APIs
    drawing.add(Rect(60, 40, 260, 30, fillColor=colors.lightpink, strokeColor=colors.black))
    drawing.add(String(190, 55, "External Data Sources", textAnchor="middle", fontSize=10))
    
    return drawing

def create_agent_flow_diagram():
    """Create agent flow diagram"""
    drawing = Drawing(400, 250)
    
    # Agent boxes
    agents = [
        (50, 200, "Agent 0\nRegistry"),
        (150, 200, "Agent 1\nSocial"),
        (250, 200, "Agent 2\nNews"),
        (50, 150, "Agent 3\nCrawl"),
        (150, 150, "Agent 4\nWeather"),
        (250, 150, "Agent 5\nFeatures"),
        (100, 100, "Agent 6\nExport"),
        (200, 100, "Agent 7\nExport")
    ]
    
    for x, y, text in agents:
        drawing.add(Rect(x, y, 80, 40, fillColor=colors.lightblue, strokeColor=colors.black))
        drawing.add(String(x + 40, y + 20, text, textAnchor="middle", fontSize=9))
    
    # Arrows (simplified as lines)
    drawing.add(String(90, 220, "→", textAnchor="middle", fontSize=16))
    drawing.add(String(190, 220, "→", textAnchor="middle", fontSize=16))
    drawing.add(String(90, 170, "→", textAnchor="middle", fontSize=16))
    drawing.add(String(190, 170, "→", textAnchor="middle", fontSize=16))
    drawing.add(String(140, 120, "→", textAnchor="middle", fontSize=16))
    
    return drawing

def create_data_flow_diagram():
    """Create data flow diagram"""
    drawing = Drawing(400, 200)
    
    # Flow boxes
    boxes = [
        (20, 150, "Seed\nData"),
        (100, 150, "Registry\nAgent"),
        (180, 150, "Geocoded\nNodes"),
        (260, 150, "Multi-Agent\nProcessing"),
        (340, 150, "Feature\nEngineering"),
        (260, 100, "Risk\nAnalysis"),
        (180, 100, "Dashboard"),
        (100, 100, "API\nServer"),
        (20, 100, "MongoDB\nStorage")
    ]
    
    for x, y, text in boxes:
        drawing.add(Rect(x, y, 60, 30, fillColor=colors.lightgreen, strokeColor=colors.black))
        drawing.add(String(x + 30, y + 15, text, textAnchor="middle", fontSize=8))
    
    # Flow arrows
    arrows = [
        (50, 165, "→"),
        (130, 165, "→"),
        (210, 165, "→"),
        (290, 165, "→"),
        (290, 145, "↓"),
        (210, 115, "←"),
        (130, 115, "←"),
        (50, 115, "←")
    ]
    
    for x, y, arrow in arrows:
        drawing.add(String(x, y, arrow, textAnchor="middle", fontSize=12))
    
    return drawing

def generate_pdf():
    """Generate the complete PDF document"""
    filename = "CERONIX_Architecture_Documentation.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=72, leftMargin=72, 
                          topMargin=72, bottomMargin=18)
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=blue
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        textColor=red
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=14,
        spaceAfter=8,
        textColor=green
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6,
        alignment=TA_JUSTIFY
    )
    
    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Code'],
        fontSize=9,
        spaceAfter=6,
        leftIndent=20
    )
    
    # Build content
    story = []
    
    # Title page
    story.append(Paragraph("CERONIX SUPPLY CHAIN RISK ANALYSIS SYSTEM", title_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Comprehensive Architecture Documentation", heading_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", body_style))
    story.append(Spacer(1, 30))
    
    # Table of Contents
    story.append(Paragraph("TABLE OF CONTENTS", heading_style))
    toc_items = [
        "1. System Overview",
        "2. High-Level Architecture",
        "3. Data Flow Architecture", 
        "4. Agent Architecture Details",
        "5. Web Architecture",
        "6. Database Architecture",
        "7. Core Services Architecture",
        "8. Orchestration Architecture",
        "9. Deployment Architecture",
        "10. API Endpoint Architecture",
        "11. Security Architecture",
        "12. Monitoring & Logging",
        "13. Technical Specifications"
    ]
    
    for item in toc_items:
        story.append(Paragraph(f"• {item}", body_style))
    
    story.append(PageBreak())
    
    # 1. System Overview
    story.append(Paragraph("1. SYSTEM OVERVIEW", heading_style))
    story.append(Paragraph(
        "The CERONIX system is a comprehensive, multi-layered architecture that combines data collection agents, "
        "real-time processing, web services, and machine learning capabilities for supply chain risk analysis. "
        "The system provides end-to-end visibility into supply chain risks through automated data collection, "
        "intelligent processing, and interactive visualization.",
        body_style
    ))
    
    story.append(Paragraph("Key Features:", subheading_style))
    features = [
        "Multi-Agent Architecture with 8 specialized agents",
        "Real-time data collection from multiple sources",
        "Google Maps integration for geocoding and location services",
        "Interactive React-based web dashboard",
        "FastAPI backend with comprehensive REST endpoints",
        "MongoDB database for scalable data storage",
        "Docker containerization for deployment",
        "Prefect-based workflow orchestration"
    ]
    
    for feature in features:
        story.append(Paragraph(f"• {feature}", body_style))
    
    story.append(PageBreak())
    
    # 2. High-Level Architecture
    story.append(Paragraph("2. HIGH-LEVEL SYSTEM ARCHITECTURE", heading_style))
    
    # Add architecture diagram
    arch_diagram = create_architecture_diagram()
    story.append(arch_diagram)
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("The system follows a layered architecture pattern with clear separation of concerns:", body_style))
    
    layers = [
        ("Frontend Layer (React)", "Interactive web dashboard with real-time updates, responsive design, and modern UI components"),
        ("API Layer (FastAPI)", "RESTful API server with WebSocket support, comprehensive endpoints, and authentication"),
        ("Data Layer (MongoDB)", "Scalable NoSQL database with collections for nodes, events, features, and analytics"),
        ("Multi-Agent Processing", "8 specialized agents for data collection, processing, and feature engineering"),
        ("Core Services", "Reusable services for geocoding, NLP, news processing, and utility functions"),
        ("External Data Sources", "Integration with Google Maps, SERP API, Weather API, Twitter API, and RSS feeds")
    ]
    
    for layer, description in layers:
        story.append(Paragraph(f"<b>{layer}:</b> {description}", body_style))
    
    story.append(PageBreak())
    
    # 3. Data Flow Architecture
    story.append(Paragraph("3. DATA FLOW ARCHITECTURE", heading_style))
    
    # Add data flow diagram
    flow_diagram = create_data_flow_diagram()
    story.append(flow_diagram)
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("Primary Data Flow:", subheading_style))
    story.append(Paragraph(
        "Seed Data → Registry Agent → Geocoded Nodes → Multi-Agent Processing → Feature Engineering → Risk Analysis → Dashboard",
        code_style
    ))
    
    story.append(Paragraph("Detailed Flow Steps:", subheading_style))
    steps = [
        "Data Ingestion: Seed supplier data from CSV files",
        "Registry Processing: Agent 0 normalizes and geocodes suppliers using Google Maps",
        "Multi-Source Collection: Agents 1-4 collect data from various sources",
        "Feature Engineering: Agent 5 processes and combines all data",
        "Export & Storage: Agents 6-7 export to CSV and store in MongoDB",
        "API Serving: FastAPI serves data to React frontend",
        "Real-time Updates: WebSocket provides live updates"
    ]
    
    for i, step in enumerate(steps, 1):
        story.append(Paragraph(f"{i}. {step}", body_style))
    
    story.append(PageBreak())
    
    # 4. Agent Architecture Details
    story.append(Paragraph("4. AGENT ARCHITECTURE DETAILS", heading_style))
    
    # Add agent flow diagram
    agent_diagram = create_agent_flow_diagram()
    story.append(agent_diagram)
    story.append(Spacer(1, 20))
    
    agents_data = [
        {
            "name": "Agent 0 - Registry Agent",
            "purpose": "Supplier registry normalization and geocoding",
            "input": "Raw supplier CSV data",
            "processing": "Data cleaning, Google Maps geocoding, duplicate detection",
            "output": "Geocoded supplier nodes",
            "dependencies": "Google Maps API, core.geo services"
        },
        {
            "name": "Agent 1 - Social Media Agent", 
            "purpose": "X/Twitter data collection",
            "input": "Supplier names and handles",
            "processing": "Twitter API integration, sentiment analysis, event extraction",
            "output": "Social media events and sentiment scores",
            "dependencies": "Twitter API, NLP services"
        },
        {
            "name": "Agent 2 - News Agent",
            "purpose": "News article collection and processing", 
            "input": "Supplier names and regions",
            "processing": "RSS feed monitoring, SERP API searches, content analysis",
            "output": "News events with sentiment and relevance scores",
            "dependencies": "SERP API, RSS feeds, NLP services"
        },
        {
            "name": "Agent 3 - Crawl Agent",
            "purpose": "Deep web crawling and content extraction",
            "input": "URLs from news and social media",
            "processing": "crawl4ai integration, HTML/PDF processing, event extraction",
            "output": "Structured events and extracted data",
            "dependencies": "crawl4ai, rate limiting services"
        },
        {
            "name": "Agent 4 - Weather Agent",
            "purpose": "Weather anomaly detection",
            "input": "Supplier locations (lat/lon)",
            "processing": "Weather API integration, anomaly detection, risk scoring",
            "output": "Weather anomalies and risk scores",
            "dependencies": "Weather API, geographic services"
        },
        {
            "name": "Agent 5 - Features Agent",
            "purpose": "ML feature engineering",
            "input": "All collected data from agents 1-4",
            "processing": "Data aggregation, feature calculation, risk score computation",
            "output": "ML-ready feature vectors",
            "dependencies": "All previous agents, core.utils"
        },
        {
            "name": "Agent 6 - Export Agent",
            "purpose": "CSV export for ML pipeline",
            "input": "Feature vectors from Agent 5",
            "processing": "Data validation, CSV formatting, file output",
            "output": "features_today.csv",
            "dependencies": "Agent 5, core.io services"
        },
        {
            "name": "Agent 7 - Export Agent (Extended)",
            "purpose": "Additional reporting and analytics",
            "input": "All processed data",
            "processing": "Report generation, analytics computation, dashboard data preparation",
            "output": "Reports and analytics data",
            "dependencies": "All agents, MongoDB"
        }
    ]
    
    for agent in agents_data:
        story.append(Paragraph(f"<b>{agent['name']}</b>", subheading_style))
        story.append(Paragraph(f"<b>Purpose:</b> {agent['purpose']}", body_style))
        story.append(Paragraph(f"<b>Input:</b> {agent['input']}", body_style))
        story.append(Paragraph(f"<b>Processing:</b> {agent['processing']}", body_style))
        story.append(Paragraph(f"<b>Output:</b> {agent['output']}", body_style))
        story.append(Paragraph(f"<b>Dependencies:</b> {agent['dependencies']}", body_style))
        story.append(Spacer(1, 10))
    
    story.append(PageBreak())
    
    # 5. Web Architecture
    story.append(Paragraph("5. WEB ARCHITECTURE", heading_style))
    
    story.append(Paragraph("Frontend Layer (React):", subheading_style))
    frontend_components = [
        "App.js - Main application component",
        "Components - Dashboard, Suppliers, Alerts, Risk Monitoring",
        "Hooks - useApiData, useWebSocket, useMetrics for data management",
        "Services - API calls, WebSocket connections, data processing",
        "Utils - Helper functions, constants, configuration",
        "Styles - CSS/SCSS with responsive design"
    ]
    
    for component in frontend_components:
        story.append(Paragraph(f"• {component}", body_style))
    
    story.append(Paragraph("Backend API Layer (FastAPI):", subheading_style))
    backend_components = [
        "main.py - Routes, middleware, CORS configuration",
        "services.py - Business logic and data processing",
        "models.py - Pydantic models for validation",
        "database.py - MongoDB connection and models",
        "WebSocket - Real-time updates and notifications",
        "Authentication - API key management and security"
    ]
    
    for component in backend_components:
        story.append(Paragraph(f"• {component}", body_style))
    
    story.append(PageBreak())
    
    # 6. Database Architecture
    story.append(Paragraph("6. DATABASE ARCHITECTURE", heading_style))
    
    story.append(Paragraph("MongoDB Collections:", subheading_style))
    collections = [
        ("nodes", "Suppliers, locations, metadata"),
        ("news_events", "Articles, sentiment, timestamps"),
        ("extracted_events", "Crawled data, structured events"),
        ("weather_anomalies", "Weather data, anomaly flags"),
        ("features", "ML data, vectors, scores"),
        ("alerts", "Warnings, critical events, notifications")
    ]
    
    for collection, description in collections:
        story.append(Paragraph(f"• <b>{collection}</b>: {description}", body_style))
    
    story.append(PageBreak())
    
    # 7. Core Services Architecture
    story.append(Paragraph("7. CORE SERVICES ARCHITECTURE", heading_style))
    
    services = [
        ("geo.py", "Geocoding, Maps API, location services"),
        ("nlp.py", "Sentiment analysis, event classification"),
        ("news.py", "RSS feeds, SERP API, content processing"),
        ("io.py", "File I/O, caching, storage management"),
        ("utils.py", "Helper functions, mathematical operations, statistics"),
        ("rate.py", "Throttling, retry logic, rate limiting"),
        ("db_models.py", "MongoDB models, queries, database operations"),
        ("schemas.py", "Validation, schemas, data types"),
        ("google_maps_geocoder.py", "Maps API integration, geocoding services")
    ]
    
    for service, description in services:
        story.append(Paragraph(f"• <b>{service}</b>: {description}", body_style))
    
    story.append(PageBreak())
    
    # 8. Orchestration Architecture
    story.append(Paragraph("8. ORCHESTRATION ARCHITECTURE", heading_style))
    
    story.append(Paragraph("Prefect Workflow Management:", subheading_style))
    orchestration_components = [
        "flow_daily.py - Daily pipeline execution and agent coordination",
        "cli.py - Command-line interface for testing, setup, and health checks",
        "Scheduler - Cron jobs, triggers, and automated execution",
        "Monitoring - Workflow status, error handling, and alerting"
    ]
    
    for component in orchestration_components:
        story.append(Paragraph(f"• {component}", body_style))
    
    story.append(PageBreak())
    
    # 9. Deployment Architecture
    story.append(Paragraph("9. DEPLOYMENT ARCHITECTURE", heading_style))
    
    story.append(Paragraph("Docker Containerization:", subheading_style))
    containers = [
        ("Backend Container", "FastAPI, Python, agents, core services"),
        ("Frontend Container", "React, Node.js, Nginx for serving"),
        ("MongoDB Container", "Database, storage, persistence")
    ]
    
    for container, description in containers:
        story.append(Paragraph(f"• <b>{container}</b>: {description}", body_style))
    
    story.append(PageBreak())
    
    # 10. API Endpoint Architecture
    story.append(Paragraph("10. API ENDPOINT ARCHITECTURE", heading_style))
    
    endpoints = [
        ("/api/health", "System health check and status"),
        ("/api/dashboard", "Dashboard data aggregation"),
        ("/api/suppliers", "Supplier management and CRUD operations"),
        ("/api/risk-factors", "Risk analysis data and metrics"),
        ("/api/routes", "Supply chain routes and logistics"),
        ("/api/alerts", "Alert management and notifications"),
        ("/api/metrics", "System metrics and performance data"),
        ("/ws/updates", "WebSocket for real-time updates")
    ]
    
    for endpoint, description in endpoints:
        story.append(Paragraph(f"• <b>{endpoint}</b>: {description}", body_style))
    
    story.append(PageBreak())
    
    # 11. Security Architecture
    story.append(Paragraph("11. SECURITY ARCHITECTURE", heading_style))
    
    security_layers = [
        ("Environment Variables", "API keys, secrets, configuration management"),
        ("API Security", "CORS, rate limiting, input validation"),
        ("Data Encryption", "MongoDB encryption, file security, network protection")
    ]
    
    for layer, description in security_layers:
        story.append(Paragraph(f"• <b>{layer}</b>: {description}", body_style))
    
    story.append(PageBreak())
    
    # 12. Monitoring & Logging
    story.append(Paragraph("12. MONITORING & LOGGING ARCHITECTURE", heading_style))
    
    monitoring_components = [
        ("Logging", "Structured JSON logs with timestamps and context"),
        ("Metrics", "Performance metrics, business metrics, system metrics"),
        ("Health Checks", "System status, component health, alerting")
    ]
    
    for component, description in monitoring_components:
        story.append(Paragraph(f"• <b>{component}</b>: {description}", body_style))
    
    story.append(PageBreak())
    
    # 13. Technical Specifications
    story.append(Paragraph("13. TECHNICAL SPECIFICATIONS", heading_style))
    
    story.append(Paragraph("Technology Stack:", subheading_style))
    tech_stack = [
        ("Frontend", "React 18, JavaScript ES6+, CSS3, WebSocket"),
        ("Backend", "FastAPI, Python 3.11+, Pydantic, Uvicorn"),
        ("Database", "MongoDB 6.0+, Motor (async driver)"),
        ("Orchestration", "Prefect 2.0+, asyncio"),
        ("APIs", "Google Maps, SERP API, Weather API, Twitter API"),
        ("Deployment", "Docker, Docker Compose, Nginx"),
        ("Monitoring", "Structured logging, health checks")
    ]
    
    for category, technologies in tech_stack:
        story.append(Paragraph(f"• <b>{category}</b>: {technologies}", body_style))
    
    story.append(Paragraph("Performance Characteristics:", subheading_style))
    performance_features = [
        "Concurrency: Async/await throughout the system",
        "Rate Limiting: Configurable per API endpoint",
        "Caching: In-memory and file-based caching strategies",
        "Scalability: Horizontal scaling ready architecture",
        "Real-time: WebSocket for live updates and notifications"
    ]
    
    for feature in performance_features:
        story.append(Paragraph(f"• {feature}", body_style))
    
    # Build PDF
    doc.build(story)
    return filename

if __name__ == "__main__":
    try:
        filename = generate_pdf()
        print(f"✅ PDF generated successfully: {filename}")
        print(f"📄 File size: {os.path.getsize(filename)} bytes")
        print(f"📁 Location: {os.path.abspath(filename)}")
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
