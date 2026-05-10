import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to attach JWT token from localStorage to all requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

const api = {
  // Authentication Endpoints
  login: (credentials) => apiClient.post('/api/auth/login', credentials).then(res => res.data),
  signup: (userData) => apiClient.post('/api/auth/signup', userData).then(res => res.data),
  googleLogin: (token) => apiClient.post('/api/auth/google', { token }).then(res => res.data),

  // Chat and Session Management
  postChat: (payload, options = {}) => 
    apiClient.post('/api/chat', payload, options).then(res => res.data),
  
  getSessions: (userId) => 
    apiClient.get(`/api/chat/sessions/${userId}`).then(res => res.data),
  
  getSessionMessages: (sessionId) => 
    apiClient.get(`/api/chat/sessions/${sessionId}/messages`).then(res => res.data),
  
  renameSession: (sessionId, title) => 
    apiClient.patch(`/api/chat/sessions/${sessionId}/rename`, { title }).then(res => res.data),
  
  deleteSession: (sessionId) => 
    apiClient.delete(`/api/chat/sessions/${sessionId}`).then(res => res.data),
  
  downloadHistory: (sessionId) => 
    apiClient.get(`/api/chat/sessions/${sessionId}/download`, { responseType: 'blob' }),

  // Wizard and Profile Endpoints
  runMatch: (payload) => apiClient.post('/api/match', payload).then(res => res.data),
  
  getProfile: (userId) => apiClient.get(`/api/profile/${userId}`).then(res => res.data),
  
  updateProfile: (userId, data) => 
    apiClient.post(`/api/profile/${userId}`, data).then(res => res.data),
  
  uploadCV: (formData) => 
    apiClient.post('/api/upload-cv', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }).then(res => res.data),

  downloadCV: (userId) => 
    apiClient.get(`/api/profile/${userId}/cv`, { responseType: 'blob' }),

  // Metrics and Human Handoff (PMF Scorecard Support)
  /**
   * Fetch system-wide PMF metrics (AI resolution rate, latency, etc.)
   * @param {number} hours - Lookback window in hours (default 336 / 2 weeks)
   */
  getMetrics: (hours = 336) => 
    apiClient.get('/api/metrics', { params: { hours } }).then(res => res.data),

  /**
   * Fetch a concise handoff summary for a student to assist a human advisor.
   * @param {string} userId - The unique identifier/email of the student.
   */
  getHandoffSummary: (userId) => 
    apiClient.get('/api/handoff-summary', { params: { user_id: userId } }).then(res => res.data),

  // Database & System Health
  getDbStatus: () => apiClient.get('/api/system/db-status').then(res => res.data),

  /**
   * Generic POST method to support components using direct endpoint calls.
   */
  post: (url, data, config) => apiClient.post(url, data, config),
};

export default api;