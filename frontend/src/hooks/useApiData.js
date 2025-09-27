import { useState, useEffect, useCallback, useMemo } from 'react';

// API base URL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Custom hook for API calls
const useApiCall = (endpoint, options = {}) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Memoize options to prevent unnecessary re-renders
  const memoizedOptions = useMemo(() => options, [JSON.stringify(options)]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const url = `${API_BASE_URL}${endpoint}`;
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...memoizedOptions.headers,
        },
        ...memoizedOptions,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err);
      console.error('API call failed:', err);
    } finally {
      setLoading(false);
    }
  }, [endpoint, memoizedOptions]);

  useEffect(() => {
    if (memoizedOptions.autoFetch !== false) {
      fetchData();
    }
  }, [fetchData, memoizedOptions.autoFetch]);

  return { data, loading, error, refetch: fetchData };
};

// Dashboard data hook with debouncing
export const useDashboardData = () => {
  const [debouncedData, setDebouncedData] = useState(null);
  const { data, loading, error, refetch } = useApiCall('/api/dashboard');

  useEffect(() => {
    if (data) {
      const timer = setTimeout(() => {
        setDebouncedData(data);
      }, 300); // 300ms debounce
      
      return () => clearTimeout(timer);
    }
  }, [data]);

  return { data: debouncedData, loading, error, refetch };
};

// Suppliers hook
export const useSuppliers = (filters = {}) => {
  const queryParams = new URLSearchParams();
  
  if (filters.country) queryParams.append('country', filters.country);
  if (filters.tier) queryParams.append('tier', filters.tier);
  if (filters.limit) queryParams.append('limit', filters.limit);

  const endpoint = `/api/suppliers${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  return useApiCall(endpoint);
};

// Risk factors hook
export const useRiskFactors = (filters = {}) => {
  const queryParams = new URLSearchParams();
  
  if (filters.severity) queryParams.append('severity', filters.severity);
  if (filters.limit) queryParams.append('limit', filters.limit);

  const endpoint = `/api/risk-factors${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  return useApiCall(endpoint);
};

// Routes hook
export const useRoutes = (filters = {}) => {
  const queryParams = new URLSearchParams();
  
  if (filters.risk_level) queryParams.append('risk_level', filters.risk_level);
  if (filters.limit) queryParams.append('limit', filters.limit);

  const endpoint = `/api/routes${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  return useApiCall(endpoint);
};

// Alerts hook
export const useAlerts = (filters = {}) => {
  const queryParams = new URLSearchParams();
  
  if (filters.severity) queryParams.append('severity', filters.severity);
  if (filters.limit) queryParams.append('limit', filters.limit);

  const endpoint = `/api/alerts${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  return useApiCall(endpoint);
};

// Metrics hook
export const useMetrics = () => {
  return useApiCall('/api/metrics');
};

// Risk analysis hook
export const useRiskAnalysis = () => {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const performAnalysis = useCallback(async (request) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/risk-analysis`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setAnalysis(result);
    } catch (err) {
      setError(err);
      console.error('Risk analysis failed:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const clearAnalysis = useCallback(() => {
    setAnalysis(null);
    setError(null);
  }, []);

  return { analysis, loading, error, performAnalysis, clearAnalysis };
};

// Real-time updates hook
export const useRealTimeUpdates = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [updateData, setUpdateData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const wsUrl = API_BASE_URL.replace('http', 'ws') + '/ws/updates';
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setIsConnected(true);
      setError(null);
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setUpdateData(data);
        setLastUpdate(new Date());
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket disconnected');
    };

    ws.onerror = (err) => {
      setError(err);
      console.error('WebSocket error:', err);
    };

    return () => {
      ws.close();
    };
  }, []);

  return { isConnected, lastUpdate, updateData, error };
};

// Health check hook
export const useHealthCheck = () => {
  return useApiCall('/api/health');
};

// Export all hooks
const apiHooks = {
  useDashboardData,
  useSuppliers,
  useRiskFactors,
  useRoutes,
  useAlerts,
  useMetrics,
  useRiskAnalysis,
  useRealTimeUpdates,
  useHealthCheck,
};

export default apiHooks;