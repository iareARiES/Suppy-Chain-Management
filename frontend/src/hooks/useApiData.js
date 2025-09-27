/**
 * Custom React hooks for API data management
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import apiService from '../services/api';

// Hook for managing API data with loading and error states
export const useApiData = (apiCall, dependencies = []) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiCall();
      setData(result);
    } catch (err) {
      setError(err);
      console.error('API call failed:', err);
    } finally {
      setLoading(false);
    }
  }, dependencies);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const refetch = useCallback(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch };
};

// Hook for suppliers data
export const useSuppliers = (filters = {}) => {
  return useApiData(
    () => apiService.getSuppliers(filters),
    [JSON.stringify(filters)]
  );
};

// Hook for risk factors data
export const useRiskFactors = (filters = {}) => {
  return useApiData(
    () => apiService.getRiskFactors(filters),
    [JSON.stringify(filters)]
  );
};

// Hook for routes data
export const useRoutes = (filters = {}) => {
  return useApiData(
    () => apiService.getRoutes(filters),
    [JSON.stringify(filters)]
  );
};

// Hook for alerts data
export const useAlerts = (filters = {}) => {
  return useApiData(
    () => apiService.getAlerts(filters),
    [JSON.stringify(filters)]
  );
};

// Hook for metrics data
export const useMetrics = () => {
  return useApiData(() => apiService.getMetrics());
};

// Hook for dashboard data
export const useDashboardData = () => {
  return useApiData(() => apiService.getDashboardData());
};

// Hook for real-time updates via WebSocket
export const useRealTimeUpdates = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [updateData, setUpdateData] = useState(null);
  const wsRef = useRef(null);

  useEffect(() => {
    // Connect to WebSocket
    const ws = apiService.connectWebSocket();
    wsRef.current = ws;

    // Add listeners
    const handleConnection = (data) => {
      setIsConnected(data.status === 'connected');
    };

    const handleMessage = (data) => {
      setLastUpdate(new Date());
      setUpdateData(data);
    };

    const handleError = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
    };

    apiService.addWebSocketListener('connection', handleConnection);
    apiService.addWebSocketListener('message', handleMessage);
    apiService.addWebSocketListener('error', handleError);

    // Cleanup
    return () => {
      apiService.removeWebSocketListener('connection', handleConnection);
      apiService.removeWebSocketListener('message', handleMessage);
      apiService.removeWebSocketListener('error', handleError);
      apiService.disconnectWebSocket();
    };
  }, []);

  return {
    isConnected,
    lastUpdate,
    updateData,
    reconnect: () => apiService.connectWebSocket()
  };
};

// Hook for risk analysis
export const useRiskAnalysis = () => {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const performAnalysis = useCallback(async (analysisRequest) => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiService.analyzeRisk(analysisRequest);
      setAnalysis(result);
      return result;
    } catch (err) {
      setError(err);
      console.error('Risk analysis failed:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const clearAnalysis = useCallback(() => {
    setAnalysis(null);
    setError(null);
  }, []);

  return {
    analysis,
    loading,
    error,
    performAnalysis,
    clearAnalysis
  };
};

// Hook for search functionality
export const useSearch = () => {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const search = useCallback(async (query, filters = {}) => {
    if (!query.trim()) {
      setResults([]);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const result = await apiService.search(query, filters);
      setResults(result.results || []);
    } catch (err) {
      setError(err);
      console.error('Search failed:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const clearResults = useCallback(() => {
    setResults([]);
    setError(null);
  }, []);

  return {
    results,
    loading,
    error,
    search,
    clearResults
  };
};

// Hook for data export
export const useExport = () => {
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState(null);

  const exportData = useCallback(async (dataType, format = 'csv', filters = {}) => {
    try {
      setExporting(true);
      setError(null);
      const result = await apiService.exportData(dataType, format, filters);
      
      // Create download link
      const link = document.createElement('a');
      link.href = result.download_url;
      link.download = result.filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      return result;
    } catch (err) {
      setError(err);
      console.error('Export failed:', err);
      throw err;
    } finally {
      setExporting(false);
    }
  }, []);

  return {
    exporting,
    error,
    exportData
  };
};

// Hook for managing component state with API integration
export const useComponentState = (initialState = {}) => {
  const [state, setState] = useState(initialState);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const updateState = useCallback((updates) => {
    setState(prev => ({ ...prev, ...updates }));
  }, []);

  const setLoadingState = useCallback((isLoading) => {
    setLoading(isLoading);
  }, []);

  const setErrorState = useCallback((err) => {
    setError(err);
  }, []);

  const resetState = useCallback(() => {
    setState(initialState);
    setLoading(false);
    setError(null);
  }, [initialState]);

  return {
    state,
    loading,
    error,
    updateState,
    setLoadingState,
    setErrorState,
    resetState
  };
};

// Hook for debounced API calls
export const useDebouncedApiCall = (apiCall, delay = 500) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const timeoutRef = useRef(null);

  const debouncedCall = useCallback((...args) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await apiCall(...args);
        setData(result);
      } catch (err) {
        setError(err);
        console.error('Debounced API call failed:', err);
      } finally {
        setLoading(false);
      }
    }, delay);
  }, [apiCall, delay]);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return {
    data,
    loading,
    error,
    debouncedCall
  };
};
