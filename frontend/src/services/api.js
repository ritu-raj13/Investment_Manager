import axios from 'axios';

// API Base URL - automatically uses environment variable in production
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Important: enables cookies/sessions for authentication
});

// Add response interceptor to handle authentication errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Unauthorized - redirect to login
      const currentPath = window.location.pathname;
      if (currentPath !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Authentication API
export const authAPI = {
  login: (username, password) => api.post('/auth/login', { username, password }),
  logout: () => api.post('/auth/logout'),
  checkAuth: () => api.get('/auth/check'),
};

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

// Health API
export const healthAPI = {
  getDashboard: () => api.get('/health/dashboard'),
  getFinancialHealth: () => api.get('/health/financial-health'), // Phase 3
};

// Recommendations API
export const recommendationsAPI = {
  getDashboard: () => api.get('/recommendations/dashboard'),
};

// Dashboard API (new - Personal Finance Manager)
export const dashboardAPI = {
  getNetWorth: () => api.get('/dashboard/net-worth'),
  getAssetAllocation: () => api.get('/dashboard/asset-allocation'),
  getCashFlow: () => api.get('/dashboard/cash-flow'),
  getSummary: () => api.get('/dashboard/summary'),
  getUnifiedXIRR: () => api.get('/dashboard/unified-xirr'), // Phase 3
};

// Mutual Funds API
export const mutualFundsAPI = {
  // Schemes
  getSchemes: () => api.get('/mutual-funds/schemes'),
  createScheme: (data) => api.post('/mutual-funds/schemes', data),
  updateScheme: (id, data) => api.put(`/mutual-funds/schemes/${id}`, data),
  deleteScheme: (id) => api.delete(`/mutual-funds/schemes/${id}`),
  fetchNav: (schemeName) => api.get(`/mutual-funds/fetch-nav/${encodeURIComponent(schemeName)}`),
  refreshNavs: () => api.post('/mutual-funds/refresh-navs'),
  
  // Transactions
  getTransactions: () => api.get('/mutual-funds/transactions'),
  createTransaction: (data) => api.post('/mutual-funds/transactions', data),
  updateTransaction: (id, data) => api.put(`/mutual-funds/transactions/${id}`, data),
  deleteTransaction: (id) => api.delete(`/mutual-funds/transactions/${id}`),
  
  // Holdings
  getHoldings: () => api.get('/mutual-funds/holdings'),
};

// Fixed Deposits API
export const fixedDepositsAPI = {
  getAll: () => api.get('/fixed-deposits'),
  create: (data) => api.post('/fixed-deposits', data),
  update: (id, data) => api.put(`/fixed-deposits/${id}`, data),
  delete: (id) => api.delete(`/fixed-deposits/${id}`),
  getMatured: () => api.get('/fixed-deposits/matured'),
  getUpcomingMaturity: () => api.get('/fixed-deposits/upcoming-maturity'),
};

// EPF API
export const epfAPI = {
  getAccounts: () => api.get('/epf/accounts'),
  createAccount: (data) => api.post('/epf/accounts', data),
  updateAccount: (id, data) => api.put(`/epf/accounts/${id}`, data),
  getContributions: () => api.get('/epf/contributions'),
  addContribution: (data) => api.post('/epf/contributions', data),
  getSummary: () => api.get('/epf/summary'),
};

// NPS API
export const npsAPI = {
  getAccounts: () => api.get('/nps/accounts'),
  createAccount: (data) => api.post('/nps/accounts', data),
  getContributions: () => api.get('/nps/contributions'),
  addContribution: (data) => api.post('/nps/contributions', data),
  getSummary: () => api.get('/nps/summary'),
};

// Savings Accounts API
export const savingsAPI = {
  getAccounts: () => api.get('/savings/accounts'),
  createAccount: (data) => api.post('/savings/accounts', data),
  updateAccount: (id, data) => api.put(`/savings/accounts/${id}`, data),
  getTransactions: () => api.get('/savings/transactions'),
  addTransaction: (data) => api.post('/savings/transactions', data),
  getSummary: () => api.get('/savings/summary'),
};

// Lending API
export const lendingAPI = {
  getAll: () => api.get('/lending'),
  create: (data) => api.post('/lending', data),
  update: (id, data) => api.put(`/lending/${id}`, data),
  getSummary: () => api.get('/lending/summary'),
};

// Other Investments API
export const otherInvestmentsAPI = {
  getAll: () => api.get('/other-investments'),
  create: (data) => api.post('/other-investments', data),
  update: (id, data) => api.put(`/other-investments/${id}`, data),
  delete: (id) => api.delete(`/other-investments/${id}`),
};

// Income API
export const incomeAPI = {
  getTransactions: () => api.get('/income/transactions'),
  createTransaction: (data) => api.post('/income/transactions', data),
  updateTransaction: (id, data) => api.put(`/income/transactions/${id}`, data),
  deleteTransaction: (id) => api.delete(`/income/transactions/${id}`),
  getSummary: () => api.get('/income/summary'),
  getCategories: () => api.get('/income/categories'),
};

// Expenses API
export const expensesAPI = {
  getTransactions: () => api.get('/expenses/transactions'),
  createTransaction: (data) => api.post('/expenses/transactions', data),
  updateTransaction: (id, data) => api.put(`/expenses/transactions/${id}`, data),
  deleteTransaction: (id) => api.delete(`/expenses/transactions/${id}`),
  getSummary: () => api.get('/expenses/summary'),
  getCategories: () => api.get('/expenses/categories'),
  getTrends: () => api.get('/expenses/trends'),
};

// Budgets API
export const budgetsAPI = {
  getAll: () => api.get('/budgets'),
  create: (data) => api.post('/budgets', data),
  update: (id, data) => api.put(`/budgets/${id}`, data),
  delete: (id) => api.delete(`/budgets/${id}`),
  getStatus: () => api.get('/budgets/status'),
};

// Global Settings API
export const globalSettingsAPI = {
  get: () => api.get('/settings/global'),
  update: (data) => api.put('/settings/global', data),
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

