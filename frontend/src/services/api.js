import axios from 'axios';

// Create axios instance
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Health check
export const healthCheck = async () => {
  try {
    const response = await api.get('/health');
    return { success: true, data: response.data };
  } catch (error) {
    return { success: false, error: error.message };
  }
};

// Component Management
export const getAvailableComponents = async () => {
  try {
    const response = await api.get('/api/components');
    return { success: true, data: response.data.components };
  } catch (error) {
    return { success: false, error: error.message };
  }
};

export const getComponentSchema = async (componentType) => {
  try {
    const response = await api.get(`/api/components/${componentType}/schema`);
    return { success: true, data: response.data };
  } catch (error) {
    return { success: false, error: error.message };
  }
};

// Workflow Management
export const createWorkflow = async (workflow) => {
  try {
    const response = await api.post('/api/workflows', workflow);
    return { success: true, data: response.data };
  } catch (error) {
    return { success: false, error: error.message };
  }
};

export const getWorkflows = async () => {
  try {
    const response = await api.get('/api/workflows');
    return { success: true, data: response.data };
  } catch (error) {
    return { success: false, error: error.message };
  }
};

export const getWorkflow = async (id) => {
  try {
    const response = await api.get(`/api/workflows/${id}`);
    return { success: true, data: response.data };
  } catch (error) {
    return { success: false, error: error.message };
  }
};

export const updateWorkflow = async (id, workflow) => {
  try {
    const response = await api.put(`/api/workflows/${id}`, workflow);
    return { success: true, data: response.data };
  } catch (error) {
    return { success: false, error: error.message };
  }
};

export const deleteWorkflow = async (id) => {
  try {
    const response = await api.delete(`/api/workflows/${id}`);
    return { success: true, data: response.data };
  } catch (error) {
    return { success: false, error: error.message };
  }
};

// Workflow Execution
export const executeWorkflow = async (workflowId, executionRequest) => {
  try {
    const response = await api.post(`/api/workflows/${workflowId}/execute`, executionRequest);
    return { success: true, data: response.data };
  } catch (error) {
    return { success: false, error: error.message };
  }
};

// Document Management
export const uploadDocument = async (file) => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    // optional collection_name can be appended by caller
    const response = await api.post('/api/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return { success: true, data: response.data };
  } catch (error) {
    return { success: false, error: error.message };
  }
};

export const getDocuments = async (collection) => {
  try {
    const response = await api.get(collection ? `/api/documents?collection=${encodeURIComponent(collection)}` : '/api/documents');
    return { success: true, data: response.data };
  } catch (error) {
    return { success: false, error: error.message };
  }
};

export const getCollections = async () => {
  try {
    const response = await api.get('/api/collections');
    return { success: true, data: response.data.collections };
  } catch (error) {
    return { success: false, error: error.message };
  }
};

// Chat
export const chatWithWorkflow = async (chatRequest) => {
  try {
    const response = await api.post('/api/chat', chatRequest);
    return { success: true, data: response.data };
  } catch (error) {
    const serverDetail = error?.response?.data?.detail;
    const message = serverDetail || error?.response?.data?.error || error.message || 'Unknown error';
    return { success: false, error: message };
  }
};

// Execution Logs
export const getExecutionLogs = async (limit = 100) => {
  try {
    const response = await api.get(`/api/executions/logs?limit=${limit}`);
    return { success: true, data: response.data.logs };
  } catch (error) {
    return { success: false, error: error.message };
  }
};

export const clearExecutionLogs = async () => {
  try {
    const response = await api.delete('/api/executions/logs');
    return { success: true, data: response.data };
  } catch (error) {
    return { success: false, error: error.message };
  }
};

export default api;
