// API service for CERONIX Supply Chain Risk Analysis Frontend
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  // Generic API call method
  async apiCall(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    
    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
      },
    };

    const config = {
      ...defaultOptions,
      ...options,
      headers: {
        ...defaultOptions.headers,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API call failed for ${endpoint}:`, error);
      throw error;
    }
  }

  // Health check
  async healthCheck() {
    return this.apiCall('/api/health');
  }

  // Dashboard data
  async getDashboardData() {
    return this.apiCall('/api/dashboard');
  }

  // Suppliers
  async getSuppliers(filters = {}) {
    const queryParams = new URLSearchParams();
    
    if (filters.country) queryParams.append('country', filters.country);
    if (filters.tier) queryParams.append('tier', filters.tier);
    if (filters.limit) queryParams.append('limit', filters.limit);

    const endpoint = `/api/suppliers${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return this.apiCall(endpoint);
  }

  async getSupplier(supplierId) {
    return this.apiCall(`/api/suppliers/${supplierId}`);
  }

  // Risk factors
  async getRiskFactors(filters = {}) {
    const queryParams = new URLSearchParams();
    
    if (filters.severity) queryParams.append('severity', filters.severity);
    if (filters.limit) queryParams.append('limit', filters.limit);

    const endpoint = `/api/risk-factors${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return this.apiCall(endpoint);
  }

  // Risk analysis
  async performRiskAnalysis(request) {
    return this.apiCall('/api/risk-analysis', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Routes
  async getRoutes(filters = {}) {
    const queryParams = new URLSearchParams();
    
    if (filters.risk_level) queryParams.append('risk_level', filters.risk_level);
    if (filters.limit) queryParams.append('limit', filters.limit);

    const endpoint = `/api/routes${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return this.apiCall(endpoint);
  }

  async getRoute(routeId) {
    return this.apiCall(`/api/routes/${routeId}`);
  }

  // Alerts
  async getAlerts(filters = {}) {
    const queryParams = new URLSearchParams();
    
    if (filters.severity) queryParams.append('severity', filters.severity);
    if (filters.limit) queryParams.append('limit', filters.limit);

    const endpoint = `/api/alerts${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return this.apiCall(endpoint);
  }

  async getRecentAlerts(hours = 24) {
    const queryParams = new URLSearchParams();
    queryParams.append('hours', hours);

    const endpoint = `/api/alerts/recent?${queryParams.toString()}`;
    return this.apiCall(endpoint);
  }

  // Metrics
  async getMetrics() {
    return this.apiCall('/api/metrics');
  }

  async getMetricTrends(days = 7) {
    const queryParams = new URLSearchParams();
    queryParams.append('days', days);

    const endpoint = `/api/metrics/trends?${queryParams.toString()}`;
    return this.apiCall(endpoint);
  }

  // WebSocket connection
  createWebSocketConnection() {
    const wsUrl = this.baseURL.replace('http', 'ws') + '/ws/updates';
    return new WebSocket(wsUrl);
  }

  // Search functionality
  async search(query, filters = {}) {
    const searchRequest = {
      query,
      filters,
      limit: filters.limit || 20,
      offset: filters.offset || 0,
    };

    return this.apiCall('/api/search', {
      method: 'POST',
      body: JSON.stringify(searchRequest),
    });
  }

  // Export functionality
  async exportData(dataType, format = 'csv', filters = {}) {
    const exportRequest = {
      data_type: dataType,
      format,
      filters,
      include_metadata: true,
    };

    return this.apiCall('/api/export', {
      method: 'POST',
      body: JSON.stringify(exportRequest),
    });
  }

  // Batch operations
  async batchGetSuppliers(supplierIds) {
    const requests = supplierIds.map(id => this.getSupplier(id));
    return Promise.all(requests);
  }

  async batchGetRoutes(routeIds) {
    const requests = routeIds.map(id => this.getRoute(id));
    return Promise.all(requests);
  }

  // Error handling utilities
  handleApiError(error, context = '') {
    console.error(`API Error ${context}:`, error);
    
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      return {
        type: 'NETWORK_ERROR',
        message: 'Unable to connect to the server. Please check your connection.',
        originalError: error,
      };
    }

    if (error.message.includes('HTTP error')) {
      const statusMatch = error.message.match(/status: (\d+)/);
      const status = statusMatch ? parseInt(statusMatch[1]) : 500;
      
      return {
        type: 'HTTP_ERROR',
        status,
        message: this.getHttpErrorMessage(status),
        originalError: error,
      };
    }

    return {
      type: 'UNKNOWN_ERROR',
      message: 'An unexpected error occurred. Please try again.',
      originalError: error,
    };
  }

  getHttpErrorMessage(status) {
    switch (status) {
      case 400:
        return 'Bad request. Please check your input.';
      case 401:
        return 'Unauthorized. Please log in again.';
      case 403:
        return 'Forbidden. You do not have permission to access this resource.';
      case 404:
        return 'Resource not found.';
      case 429:
        return 'Too many requests. Please wait a moment and try again.';
      case 500:
        return 'Internal server error. Please try again later.';
      case 502:
        return 'Bad gateway. The server is temporarily unavailable.';
      case 503:
        return 'Service unavailable. Please try again later.';
      default:
        return `HTTP error ${status}. Please try again.`;
    }
  }

  // Retry mechanism
  async apiCallWithRetry(endpoint, options = {}, maxRetries = 3) {
    let lastError;
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await this.apiCall(endpoint, options);
      } catch (error) {
        lastError = error;
        
        if (attempt === maxRetries) {
          throw error;
        }

        // Wait before retrying (exponential backoff)
        const delay = Math.pow(2, attempt) * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
        
        console.warn(`API call failed (attempt ${attempt}), retrying in ${delay}ms...`);
      }
    }
    
    throw lastError;
  }

  // Cache management
  constructor() {
    this.baseURL = API_BASE_URL;
    this.cache = new Map();
    this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
  }

  getCacheKey(endpoint, options = {}) {
    return `${endpoint}_${JSON.stringify(options)}`;
  }

  getFromCache(key) {
    const cached = this.cache.get(key);
    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      return cached.data;
    }
    this.cache.delete(key);
    return null;
  }

  setCache(key, data) {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
    });
  }

  clearCache() {
    this.cache.clear();
  }

  // Cached API call
  async cachedApiCall(endpoint, options = {}) {
    const cacheKey = this.getCacheKey(endpoint, options);
    const cached = this.getFromCache(cacheKey);
    
    if (cached) {
      return cached;
    }

    const data = await this.apiCall(endpoint, options);
    this.setCache(cacheKey, data);
    return data;
  }
}

// Create and export singleton instance
const apiService = new ApiService();
export default apiService;

// Export individual methods for convenience
export const {
  healthCheck,
  getDashboardData,
  getSuppliers,
  getSupplier,
  getRiskFactors,
  performRiskAnalysis,
  getRoutes,
  getRoute,
  getAlerts,
  getRecentAlerts,
  getMetrics,
  getMetricTrends,
  createWebSocketConnection,
  search,
  exportData,
  batchGetSuppliers,
  batchGetRoutes,
  handleApiError,
  apiCallWithRetry,
  cachedApiCall,
  clearCache,
} = apiService;