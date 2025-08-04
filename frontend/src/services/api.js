import axios from 'axios';

// const API_BASE_URL = import.meta.env.RAILWAY_PUBLIC_DOMAIN || 'http://localhost:8080/api/v1';


const API_BASE_URL ='https://open-pair-production.up.railway.app/'

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth tokens (if needed)
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for handling errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API endpoints
export const agentsAPI = {
  getAll: (params = {}) => api.get('/agents', { params }),
  getById: (id) => api.get(`/agents/${id}`),
  create: (data) => api.post('/agents', data),
  update: (id, data) => api.put(`/agents/${id}`, data),
  delete: (id) => api.delete(`/agents/${id}`),
  getAvailability: (id) => api.get(`/agents/${id}/availability`),
  addAvailability: (id, data) => api.post(`/agents/${id}/availability`, data),
  removeAvailability: (id, availabilityId) => api.delete(`/agents/${id}/availability/${availabilityId}`),
  getPerformance: (id, params = {}) => api.get(`/agents/${id}/performance`, { params }),
  getFairnessScore: (id) => api.get(`/agents/${id}/fairness-score`),
  searchByArea: (params) => api.get('/agents/search/by-area', { params }),
  searchByPriceRange: (params) => api.get('/agents/search/by-price-range', { params }),
};

export const listingsAPI = {
  getAll: (params = {}) => api.get('/listings', { params }),
  getById: (id) => api.get(`/listings/${id}`),
  create: (data) => api.post('/listings', data),
  update: (id, data) => api.put(`/listings/${id}`, data),
  delete: (id) => api.delete(`/listings/${id}`),
  getByMLS: (mlsNumber) => api.get(`/listings/search/by-mls/${mlsNumber}`),
  getByAgent: (agentId, params = {}) => api.get(`/listings/agent/${agentId}`, { params }),
  getStats: () => api.get('/listings/stats/summary'),
};

export const openHousesAPI = {
  getAll: (params = {}) => api.get('/open-houses', { params }),
  getById: (id) => api.get(`/open-houses/${id}`),
  create: (data) => api.post('/open-houses', data),
  update: (id, data) => api.put(`/open-houses/${id}`, data),
  cancel: (id) => api.delete(`/open-houses/${id}`),
  generateRecommendations: (id) => api.post(`/open-houses/${id}/generate-recommendations`),
  submitFeedback: (id, data) => api.post(`/open-houses/${id}/feedback`, data),
  getFeedback: (id) => api.get(`/open-houses/${id}/feedback`),
  complete: (id) => api.post(`/open-houses/${id}/complete`),
  getUpcomingWeek: () => api.get('/open-houses/upcoming/week'),
};

export const dashboardAPI = {
  getStats: () => api.get('/dashboard/stats'),
  getWeeklySummary: () => api.get('/dashboard/weekly-summary'),
  sendWeeklyEmail: (recipients) => api.post('/dashboard/send-weekly-email', { recipients }),
  getFairnessReport: () => api.get('/dashboard/fairness-report'),
  retrainModel: () => api.post('/dashboard/retrain-model'),
  getModelPerformance: () => api.get('/dashboard/model-performance'),
  getUpcomingUnassigned: (daysAhead = 7) => api.get(`/dashboard/upcoming-unassigned?days_ahead=${daysAhead}`),
};

export default api;
