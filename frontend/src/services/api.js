import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Stock Tracking API
export const stockAPI = {
  getAll: () => api.get('/stocks'),
  getById: (id) => api.get(`/stocks/${id}`),
  create: (data) => api.post('/stocks', data),
  update: (id, data) => api.put(`/stocks/${id}`, data),
  delete: (id) => api.delete(`/stocks/${id}`),
  refreshPrices: () => api.post('/stocks/refresh-prices'),
  refreshAlertStocks: () => api.post('/stocks/refresh-alert-stocks'),
  getGroups: () => api.get('/stocks/groups'),
  getSectors: () => api.get('/stocks/sectors'),
  fetchDetails: (symbol) => api.get(`/stocks/fetch-details/${symbol}`),
};

// Portfolio API
export const portfolioAPI = {
  getTransactions: () => api.get('/portfolio/transactions'),
  createTransaction: (data) => api.post('/portfolio/transactions', data),
  updateTransaction: (id, data) => api.put(`/portfolio/transactions/${id}`, data),
  deleteTransaction: (id) => api.delete(`/portfolio/transactions/${id}`),
  getSummary: () => api.get('/portfolio/summary'),
  getSettings: () => api.get('/portfolio/settings'),
  updateSettings: (data) => api.put('/portfolio/settings', data),
};

// Analytics API
export const analyticsAPI = {
  getDashboard: () => api.get('/analytics/dashboard'),
};

// Import/Export & Backup/Restore API
export const dataAPI = {
  // Export
  exportStocks: () => api.get('/export/stocks', { responseType: 'blob' }),
  exportTransactions: () => api.get('/export/transactions', { responseType: 'blob' }),
  backupDatabase: () => api.get('/backup/database', { responseType: 'blob' }),
  
  // Import
  importStocks: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/import/stocks', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  importTransactions: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/import/transactions', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  restoreDatabase: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/restore/database', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
};

export default api;

