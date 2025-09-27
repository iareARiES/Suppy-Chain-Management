/**
 * API service layer for CERONIX Supply Chain Risk Analysis
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
const WS_BASE_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
    this.wsURL = WS_BASE_URL;
    this.wsConnection = null;
    this.wsListeners = new Map();
  }

  // Generic HTTP request method
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      throw error;
    }
  }

  // Health check
  async healthCheck() {
    return this.request('/health');
  }

  // Supplier endpoints
  async getSuppliers(filters = {}) {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== null && value !== undefined) {
        params.append(key, value);
      }
    });
    
    const queryString = params.toString();
    const endpoint = queryString ? `/suppliers?${queryString}` : '/suppliers';
    return this.request(endpoint);
  }

  async getSupplier(supplierId) {
    return this.request(`/suppliers/${supplierId}`);
  }

  // Risk analysis endpoints
  async getRiskFactors(filters = {}) {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== null && value !== undefined) {
        params.append(key, value);
      }
    });
    
    const queryString = params.toString();
    const endpoint = queryString ? `/risk-factors?${queryString}` : '/risk-factors';
    return this.request(endpoint);
  }

  async analyzeRisk(analysisRequest) {
    return this.request('/risk-analysis', {
      method: 'POST',
      body: JSON.stringify(analysisRequest),
    });
  }

  // Route endpoints
  async getRoutes(filters = {}) {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== null && value !== undefined) {
        params.append(key, value);
      }
    });
    
    const queryString = params.toString();
    const endpoint = queryString ? `/routes?${queryString}` : '/routes';
    return this.request(endpoint);
  }

  async getRoute(routeId) {
    return this.request(`/routes/${routeId}`);
  }

  // Alert endpoints
  async getAlerts(filters = {}) {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== null && value !== undefined) {
        params.append(key, value);
      }
    });
    
    const queryString = params.toString();
    const endpoint = queryString ? `/alerts?${queryString}` : '/alerts';
    return this.request(endpoint);
  }

  async getRecentAlerts(hours = 24) {
    return this.request(`/alerts/recent?hours=${hours}`);
  }

  // Metrics endpoints
  async getMetrics() {
    return this.request('/metrics');
  }

  async getMetricTrends(days = 7) {
    return this.request(`/metrics/trends?days=${days}`);
  }

  // WebSocket connection management
  connectWebSocket() {
    if (this.wsConnection && this.wsConnection.readyState === WebSocket.OPEN) {
      return this.wsConnection;
    }

    this.wsConnection = new WebSocket(this.wsURL + '/updates');
    
    this.wsConnection.onopen = () => {
      console.log('WebSocket connected');
      this.notifyListeners('connection', { status: 'connected' });
    };

    this.wsConnection.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.notifyListeners('message', data);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    this.wsConnection.onclose = () => {
      console.log('WebSocket disconnected');
      this.notifyListeners('connection', { status: 'disconnected' });
      
      // Attempt to reconnect after 5 seconds
      setTimeout(() => {
        if (this.wsConnection.readyState === WebSocket.CLOSED) {
          this.connectWebSocket();
        }
      }, 5000);
    };

    this.wsConnection.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.notifyListeners('error', error);
    };

    return this.wsConnection;
  }

  disconnectWebSocket() {
    if (this.wsConnection) {
      this.wsConnection.close();
      this.wsConnection = null;
    }
  }

  // WebSocket event listeners
  addWebSocketListener(event, callback) {
    if (!this.wsListeners.has(event)) {
      this.wsListeners.set(event, []);
    }
    this.wsListeners.get(event).push(callback);
  }

  removeWebSocketListener(event, callback) {
    if (this.wsListeners.has(event)) {
      const listeners = this.wsListeners.get(event);
      const index = listeners.indexOf(callback);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  }

  notifyListeners(event, data) {
    if (this.wsListeners.has(event)) {
      this.wsListeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('Error in WebSocket listener:', error);
        }
      });
    }
  }

  // Utility methods
  async getDashboardData() {
    try {
      const [metrics, riskFactors, routes, alerts, suppliers] = await Promise.all([
        this.getMetrics(),
        this.getRiskFactors({ limit: 10 }),
        this.getRoutes({ limit: 10 }),
        this.getRecentAlerts(24),
        this.getSuppliers({ limit: 20 })
      ]);

      return {
        metrics,
        riskFactors,
        routes,
        alerts,
        suppliers,
        lastUpdated: new Date().toISOString()
      };
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      throw error;
    }
  }

  // Search functionality
  async search(query, filters = {}) {
    return this.request('/search', {
      method: 'POST',
      body: JSON.stringify({ query, filters }),
    });
  }

  // Export functionality
  async exportData(dataType, format = 'csv', filters = {}) {
    return this.request('/export', {
      method: 'POST',
      body: JSON.stringify({ data_type: dataType, format, filters }),
    });
  }
}

// Create and export a singleton instance
const apiService = new ApiService();
export default apiService;

// Export individual methods for convenience
export const {
  healthCheck,
  getSuppliers,
  getSupplier,
  getRiskFactors,
  analyzeRisk,
  getRoutes,
  getRoute,
  getAlerts,
  getRecentAlerts,
  getMetrics,
  getMetricTrends,
  connectWebSocket,
  disconnectWebSocket,
  addWebSocketListener,
  removeWebSocketListener,
  getDashboardData,
  search,
  exportData
} = apiService;
