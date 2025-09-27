import React, { useState, useEffect } from 'react';
import './App.css';

// Import API hooks
import { 
  useDashboardData, 
  useRealTimeUpdates, 
  useRiskAnalysis,
  useSuppliers,
  useRiskFactors,
  useRoutes,
  useAlerts,
  useMetrics
} from './hooks/useApiData';

// Simple SVG icon components
const AlertTriangle = ({ size = 20, className = "" }) => (
  <svg width={size} height={size} className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>
    <path d="M12 9v4"/>
    <path d="m12 17 .01 0"/>
  </svg>
);

const Shield = ({ size = 20, className = "" }) => (
  <svg width={size} height={size} className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M20 13c0 5-3.5 7.5-8 7.5s-8-2.5-8-7.5c0-1.3.3-2.3.8-3.2L12 3l7.2 6.8c.5.9.8 1.9.8 3.2Z"/>
  </svg>
);

const MapPin = ({ size = 20, className = "" }) => (
  <svg width={size} height={size} className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/>
    <circle cx="12" cy="10" r="3"/>
  </svg>
);

const Package = ({ size = 20, className = "" }) => (
  <svg width={size} height={size} className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="m7.5 4.27 9 5.15"/>
    <path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/>
    <path d="m3.3 7 8.7 5 8.7-5"/>
    <path d="M12 22V12"/>
  </svg>
);

const TrendingUp = ({ size = 20, className = "" }) => (
  <svg width={size} height={size} className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="22,7 13.5,15.5 8.5,10.5 2,17"/>
    <polyline points="16,7 22,7 22,13"/>
  </svg>
);

const Cloud = ({ size = 20, className = "" }) => (
  <svg width={size} height={size} className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/>
  </svg>
);

const Users = ({ size = 20, className = "" }) => (
  <svg width={size} height={size} className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
    <circle cx="9" cy="7" r="4"/>
    <path d="m22 21-3.5-3.5"/>
    <circle cx="20" cy="8" r="3"/>
  </svg>
);

const Building = ({ size = 20, className = "" }) => (
  <svg width={size} height={size} className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect width="16" height="20" x="4" y="2" rx="2" ry="2"/>
    <path d="M9 22v-4h6v4"/>
    <path d="M8 6h.01"/>
    <path d="M16 6h.01"/>
    <path d="M12 6h.01"/>
    <path d="M12 10h.01"/>
    <path d="M12 14h.01"/>
    <path d="M16 10h.01"/>
    <path d="M16 14h.01"/>
    <path d="M8 10h.01"/>
    <path d="M8 14h.01"/>
  </svg>
);

const Globe = ({ size = 20, className = "" }) => (
  <svg width={size} height={size} className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="12" cy="12" r="10"/>
    <path d="m2 12 20 0"/>
    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
  </svg>
);

const ChevronRight = ({ size = 20, className = "" }) => (
  <svg width={size} height={size} className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="m9 18 6-6-6-6"/>
  </svg>
);

const Search = ({ size = 20, className = "" }) => (
  <svg width={size} height={size} className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="11" cy="11" r="8"/>
    <path d="m21 21-4.35-4.35"/>
  </svg>
);

const Bell = ({ size = 20, className = "" }) => (
  <svg width={size} height={size} className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/>
    <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>
  </svg>
);

const Settings = ({ size = 20, className = "" }) => (
  <svg width={size} height={size} className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/>
    <circle cx="12" cy="12" r="3"/>
  </svg>
);

const BarChart3 = ({ size = 20, className = "" }) => (
  <svg width={size} height={size} className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M3 3v18h18"/>
    <path d="M18 17V9"/>
    <path d="M13 17V5"/>
    <path d="M8 17v-3"/>
  </svg>
);

const Route = ({ size = 20, className = "" }) => (
  <svg width={size} height={size} className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="6" cy="19" r="3"/>
    <path d="M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15"/>
    <circle cx="18" cy="5" r="3"/>
  </svg>
);

const Zap = ({ size = 20, className = "" }) => (
  <svg width={size} height={size} className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polygon points="13,2 3,14 12,14 11,22 21,10 12,10 13,2"/>
  </svg>
);

const LoadingSpinner = ({ size = 20, className = "" }) => (
  <svg width={size} height={size} className={`animate-spin ${className}`} viewBox="0 0 24 24" fill="none">
    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" className="opacity-25"/>
    <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" className="opacity-75"/>
  </svg>
);

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedComponent, setSelectedComponent] = useState('');
  const [sellerLocation, setSellerLocation] = useState('');
  const [importLocation, setImportLocation] = useState('');

  // API data hooks
  const { data: dashboardData, loading: dashboardLoading, error: dashboardError, refetch: refetchDashboard } = useDashboardData();
  const { isConnected: wsConnected, lastUpdate, updateData } = useRealTimeUpdates();
  const { analysis, loading: analysisLoading, performAnalysis, clearAnalysis } = useRiskAnalysis();

  // Individual data hooks for fallback
  const { data: suppliers, loading: suppliersLoading } = useSuppliers({ limit: 20 });
  const { data: riskFactors, loading: riskFactorsLoading } = useRiskFactors({ limit: 10 });
  const { data: routes, loading: routesLoading } = useRoutes({ limit: 10 });
  const { data: alerts, loading: alertsLoading } = useAlerts({ limit: 10 });
  const { data: metrics, loading: metricsLoading } = useMetrics();

  // Use dashboard data if available, otherwise fall back to individual data
  const currentData = dashboardData || {
    suppliers: suppliers || [],
    riskFactors: riskFactors || [],
    routes: routes || [],
    alerts: alerts || [],
    metrics: metrics || {}
  };

  // Real-time data updates
  useEffect(() => {
    if (updateData && updateData.type === 'metrics_update') {
      // Update metrics in real-time
      console.log('Real-time update received:', updateData);
      // You could update local state here or trigger a refetch
    }
  }, [updateData]);

  const handleRiskAnalysis = async () => {
    if (!selectedComponent || !sellerLocation || !importLocation) {
      alert('Please fill in all required fields');
      return;
    }

    try {
      const analysisRequest = {
        component_type: selectedComponent,
        seller_location: sellerLocation,
        import_location: importLocation,
        quantity: 1,
        urgency: 'normal'
      };

      await performAnalysis(analysisRequest);
    } catch (error) {
      console.error('Risk analysis failed:', error);
    }
  };

  const TabButton = ({ id, label, icon: Icon, active, onClick }) => (
    <button
      onClick={() => onClick(id)}
      className={`tab-button ${active ? 'tab-button--active' : ''}`}
    >
      <Icon size={18} className="tab-icon" />
      {label}
    </button>
  );

  const MetricCard = ({ title, value, subtitle, icon: Icon, trend, loading: cardLoading }) => (
    <div className="metric-card">
      <div className="metric-card__header">
        <div className="metric-card__icon">
          {cardLoading ? <LoadingSpinner size={20} /> : <Icon size={20} />}
        </div>
        {trend && (
          <div className="metric-card__trend">
            <TrendingUp size={16} />
            {trend}
          </div>
        )}
      </div>
      <div className="metric-card__value">
        {cardLoading ? '...' : value}
      </div>
      <div className="metric-card__subtitle">{subtitle}</div>
    </div>
  );

  const RiskFactorCard = ({ factor, loading: cardLoading }) => (
    <div className="risk-factor-card">
      <div className="risk-factor-card__header">
        <div className="risk-factor-card__info">
          <div className="risk-factor-card__icon">
            {cardLoading ? <LoadingSpinner size={20} /> : <Cloud size={20} />}
          </div>
          <div className="risk-factor-card__details">
            <h3 className="risk-factor-card__title">{factor.name}</h3>
            <span className={`risk-level risk-level--${factor.level.toLowerCase()}`}>
              {factor.level} Risk
            </span>
          </div>
        </div>
        <div className="risk-factor-card__impact">
          <div className="risk-factor-card__impact-value">{factor.impact}%</div>
          <div className="risk-factor-card__impact-label">Impact</div>
        </div>
      </div>
      <p className="risk-factor-card__description">{factor.description}</p>
      <div className="risk-factor-card__progress">
        <div 
          className={`risk-factor-card__progress-bar risk-factor-card__progress-bar--${factor.level.toLowerCase()}`}
          style={{ width: `${factor.impact}%` }}
        />
      </div>
    </div>
  );

  const RouteCard = ({ route, loading: cardLoading }) => (
    <div className="route-card">
      <div className="route-card__header">
        <div className="route-card__info">
          <Route size={20} className="route-card__icon" />
          <div className="route-card__details">
            <h3 className="route-card__title">{route.name}</h3>
            <span className={`risk-level risk-level--${route.risk_level.toLowerCase()}`}>
              {route.risk_level} Risk
            </span>
          </div>
        </div>
        <button className="route-card__button">
          <ChevronRight size={20} />
        </button>
      </div>
      <div className="route-card__stats">
        <div className="route-card__stat">
          <div className="route-card__stat-value">{route.duration_days} days</div>
          <div className="route-card__stat-label">Duration</div>
        </div>
        <div className="route-card__stat">
          <div className="route-card__stat-value">${route.cost_usd.toLocaleString()}</div>
          <div className="route-card__stat-label">Cost</div>
        </div>
        <div className="route-card__stat">
          <div className="route-card__stat-value">{route.reliability_percentage}%</div>
          <div className="route-card__stat-label">Reliability</div>
        </div>
      </div>
    </div>
  );

  const AlertItem = ({ alert, loading: cardLoading }) => (
    <div className={`alert-item alert-item--${alert.severity.toLowerCase()}`}>
      <AlertTriangle size={20} className="alert-item__icon" />
      <div className="alert-item__content">
        <div className="alert-item__title">{alert.title}</div>
        <div className="alert-item__description">{alert.message}</div>
      </div>
    </div>
  );

  return (
    <div className="dashboard">
      {/* Header */}
      <header className="header">
        <div className="header__content">
          <div className="header__brand">
            <Shield size={28} className="header__logo" />
            <h1 className="header__title">Supply Chain Intelligence</h1>
            {wsConnected && (
              <div className="header__status">
                <div className="status-indicator status-indicator--connected"></div>
                <span>Live</span>
              </div>
            )}
          </div>
          <div className="header__actions">
            <div className="search-container">
              <Search size={20} className="search-icon" />
              <input 
                type="text" 
                placeholder="Search routes, components..."
                className="search-input"
              />
            </div>
            <button className="header__action-button">
              <Bell size={20} />
            </button>
            <button className="header__action-button">
              <Settings size={20} />
            </button>
          </div>
        </div>
      </header>

      <div className="dashboard__container">
        {/* Navigation Tabs */}
        <div className="tab-navigation">
          <TabButton 
            id="overview" 
            label="Overview" 
            icon={BarChart3}
            active={activeTab === 'overview'} 
            onClick={setActiveTab} 
          />
          <TabButton 
            id="analysis" 
            label="Risk Analysis" 
            icon={AlertTriangle}
            active={activeTab === 'analysis'} 
            onClick={setActiveTab} 
          />
          <TabButton 
            id="routes" 
            label="Route Planning" 
            icon={MapPin}
            active={activeTab === 'routes'} 
            onClick={setActiveTab} 
          />
          <TabButton 
            id="monitoring" 
            label="Real-time Monitoring" 
            icon={Zap}
            active={activeTab === 'monitoring'} 
            onClick={setActiveTab} 
          />
        </div>

        {/* Error Display */}
        {dashboardError && (
          <div className="error-banner">
            <AlertTriangle size={20} />
            <span>Failed to load data: {dashboardError.message}</span>
            <button onClick={refetchDashboard} className="retry-button">Retry</button>
          </div>
        )}

        {activeTab === 'overview' && (
          <div className="dashboard__content">
            {/* Component Input Section */}
            <div className="configuration-panel">
              <h2 className="configuration-panel__title">Supply Chain Configuration</h2>
              <div className="configuration-panel__form">
                <div className="form-field">
                  <label className="form-field__label">Component Type</label>
                  <select 
                    value={selectedComponent}
                    onChange={(e) => setSelectedComponent(e.target.value)}
                    className="form-field__select"
                  >
                    <option value="">Select Component</option>
                    <option value="semiconductors">Semiconductors</option>
                    <option value="batteries">Lithium Batteries</option>
                    <option value="steel">Steel Components</option>
                    <option value="electronics">Electronic Parts</option>
                    <option value="textiles">Textiles</option>
                  </select>
                </div>
                <div className="form-field">
                  <label className="form-field__label">Seller Location</label>
                  <input 
                    type="text" 
                    value={sellerLocation}
                    onChange={(e) => setSellerLocation(e.target.value)}
                    placeholder="Enter seller location"
                    className="form-field__input"
                  />
                </div>
                <div className="form-field">
                  <label className="form-field__label">Import Location</label>
                  <input 
                    type="text" 
                    value={importLocation}
                    onChange={(e) => setImportLocation(e.target.value)}
                    placeholder="Enter import destination"
                    className="form-field__input"
                  />
                </div>
              </div>
              <button 
                className="configuration-panel__button"
                onClick={handleRiskAnalysis}
                disabled={analysisLoading}
              >
                {analysisLoading ? (
                  <>
                    <LoadingSpinner size={16} />
                    Analyzing...
                  </>
                ) : (
                  'Analyze Supply Chain Risk'
                )}
              </button>
            </div>

            {/* Analysis Results */}
            {analysis && (
              <div className="analysis-results">
                <h3>Risk Analysis Results</h3>
                <div className="analysis-summary">
                  <div className="analysis-metric">
                    <span className="analysis-metric__label">Overall Risk Score</span>
                    <span className="analysis-metric__value">{analysis.overall_risk_score}/100</span>
                  </div>
                  <div className="analysis-metric">
                    <span className="analysis-metric__label">Risk Level</span>
                    <span className={`analysis-metric__value risk-level--${analysis.risk_level.toLowerCase()}`}>
                      {analysis.risk_level}
                    </span>
                  </div>
                  <div className="analysis-metric">
                    <span className="analysis-metric__label">Confidence</span>
                    <span className="analysis-metric__value">{analysis.confidence}%</span>
                  </div>
                </div>
                <button onClick={clearAnalysis} className="clear-analysis-button">
                  Clear Analysis
                </button>
              </div>
            )}

            {/* Metrics Overview */}
            <div className="metrics-grid">
              <MetricCard 
                title="Overall Risk Score"
                value={currentData.metrics?.overall_risk_score ? `${currentData.metrics.overall_risk_score}/100` : 'N/A'}
                subtitle="Medium Risk Level"
                icon={Shield}
                trend="+5%"
                loading={metricsLoading}
              />
              <MetricCard 
                title="Active Routes"
                value={currentData.metrics?.active_routes || 'N/A'}
                subtitle="Monitored Pathways"
                icon={Route}
                trend="+12%"
                loading={routesLoading}
              />
              <MetricCard 
                title="Disruption Alerts"
                value={currentData.metrics?.active_alerts || 'N/A'}
                subtitle="Last 24 hours"
                icon={AlertTriangle}
                loading={alertsLoading}
              />
              <MetricCard 
                title="Reliability Score"
                value={currentData.metrics?.reliability_score ? `${currentData.metrics.reliability_score}%` : 'N/A'}
                subtitle="On-time Delivery Rate"
                icon={TrendingUp}
                trend="+3%"
                loading={metricsLoading}
              />
            </div>

            {/* Risk Factors Grid */}
            <div className="risk-factors-grid">
              {riskFactorsLoading ? (
                <div className="loading-placeholder">Loading risk factors...</div>
              ) : (
                currentData.riskFactors?.map(factor => (
                  <RiskFactorCard key={factor.id} factor={factor} />
                ))
              )}
            </div>
          </div>
        )}

        {activeTab === 'analysis' && (
          <div className="dashboard__content">
            <div className="analysis-panel">
              <h2 className="analysis-panel__title">Comprehensive Risk Analysis</h2>
              <div className="analysis-panel__content">
                <div className="analysis-section">
                  <h3 className="analysis-section__title">Risk Distribution</h3>
                  <div className="analysis-section__items">
                    {riskFactorsLoading ? (
                      <div className="loading-placeholder">Loading analysis...</div>
                    ) : (
                      currentData.riskFactors?.map(factor => (
                        <div key={factor.id} className="analysis-item">
                          <div className="analysis-item__header">
                            <span className="analysis-item__name">{factor.name}</span>
                            <span className={`analysis-item__impact risk-level--${factor.level.toLowerCase()}`}>
                              {factor.impact}%
                            </span>
                          </div>
                          <div className="analysis-item__progress">
                            <div 
                              className={`analysis-item__progress-bar risk-level--${factor.level.toLowerCase()}`}
                              style={{ width: `${factor.impact}%` }}
                            />
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
                <div className="analysis-section">
                  <h3 className="analysis-section__title">Mitigation Strategies</h3>
                  <div className="analysis-section__items">
                    <div className="strategy-item">
                      <h4 className="strategy-item__title">Weather Risk Mitigation</h4>
                      <p className="strategy-item__description">Deploy alternative routes during severe weather conditions and maintain buffer inventory.</p>
                    </div>
                    <div className="strategy-item">
                      <h4 className="strategy-item__title">Labor Strike Contingency</h4>
                      <p className="strategy-item__description">Establish partnerships with alternative ports and logistics providers.</p>
                    </div>
                    <div className="strategy-item">
                      <h4 className="strategy-item__title">Sanctions Compliance</h4>
                      <p className="strategy-item__description">Regular monitoring of international trade regulations and pre-approved alternative suppliers.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'routes' && (
          <div className="dashboard__content">
            <div className="map-panel">
              <h2 className="map-panel__title">Interactive Route Map</h2>
              <div className="map-placeholder">
                <MapPin size={48} className="map-placeholder__icon" />
                <h3 className="map-placeholder__title">Interactive Map View</h3>
                <p className="map-placeholder__description">
                  Map integration would display real-time route analysis with risk indicators, 
                  safe corridors highlighted in green, and high-risk areas marked in red.
                </p>
                <button className="map-placeholder__button">
                  Launch Full Map View
                </button>
              </div>
            </div>

            <div className="routes-grid">
              {routesLoading ? (
                <div className="loading-placeholder">Loading routes...</div>
              ) : (
                currentData.routes?.map(route => (
                  <RouteCard key={route.id} route={route} />
                ))
              )}
            </div>
          </div>
        )}

        {activeTab === 'monitoring' && (
          <div className="dashboard__content">
            <div className="monitoring-grid">
              <div className="alerts-panel">
                <h3 className="alerts-panel__title">Real-time Alerts</h3>
                <div className="alerts-panel__items">
                  {alertsLoading ? (
                    <div className="loading-placeholder">Loading alerts...</div>
                  ) : (
                    currentData.alerts?.map(alert => (
                      <AlertItem key={alert.id} alert={alert} />
                    ))
                  )}
                </div>
              </div>

              <div className="tracking-panel">
                <h3 className="tracking-panel__title">Live Tracking</h3>
                <div className="tracking-panel__items">
                  <div className="tracking-item">
                    <div className="tracking-item__info">
                      <Package size={20} className="tracking-item__icon" />
                      <div className="tracking-item__details">
                        <div className="tracking-item__title">Shipment #SC2024-001</div>
                        <div className="tracking-item__description">In Transit - 65% Complete</div>
                      </div>
                    </div>
                    <div className="tracking-item__status tracking-item__status--success">On Time</div>
                  </div>
                  <div className="tracking-item">
                    <div className="tracking-item__info">
                      <Package size={20} className="tracking-item__icon" />
                      <div className="tracking-item__details">
                        <div className="tracking-item__title">Shipment #SC2024-002</div>
                        <div className="tracking-item__description">Delayed - Weather</div>
                      </div>
                    </div>
                    <div className="tracking-item__status tracking-item__status--danger">2 Days Late</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
