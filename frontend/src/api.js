const API_BASE = '/api';

export async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  const config = {
    ...options,
    headers,
    credentials: 'include', // Ensures Django session cookies are transmitted
  };

  if (options.body && typeof options.body === 'object') {
    config.body = JSON.stringify(options.body);
  }

  try {
    const response = await fetch(url, config);
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      const errorMsg = data.message || `Request failed with status ${response.status}`;
      throw new Error(errorMsg);
    }
    return data;
  } catch (err) {
    console.error(`API Error on ${endpoint}:`, err);
    throw err;
  }
}

export const api = {
  // Auth
  getMe: () => apiRequest('/auth/me/'),
  login: (email, password) => apiRequest('/auth/login/', { method: 'POST', body: { email, password } }),
  logout: () => apiRequest('/auth/logout/', { method: 'POST' }),
  register: (payload) => apiRequest('/auth/register/', { method: 'POST', body: payload }),

  // Dashboard
  getDashboard: () => apiRequest('/dashboard/'),

  // Subscriptions
  getSubscriptions: (status = '') => apiRequest(`/subscriptions/${status ? `?status=${status}` : ''}`),
  getSubscription: (uuid) => apiRequest(`/subscriptions/${uuid}/`),
  createSubscription: (payload) => apiRequest('/subscriptions/create/', { method: 'POST', body: payload }),
  transitionSubscription: (uuid, action, reason = '') =>
    apiRequest(`/subscriptions/${uuid}/transition/`, { method: 'POST', body: { action, reason } }),

  // Invoices & Billing
  getInvoices: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return apiRequest(`/invoices/${query ? `?${query}` : ''}`);
  },
  getInvoice: (uuid) => apiRequest(`/invoices/${uuid}/`),
  recordPayment: (uuid, payload) => apiRequest(`/invoices/${uuid}/pay/`, { method: 'POST', body: payload }),
  confirmInvoice: (uuid) => apiRequest(`/invoices/${uuid}/confirm/`, { method: 'POST' }),
  voidInvoice: (uuid, reason) => apiRequest(`/invoices/${uuid}/void/`, { method: 'POST', body: { reason } }),
  runBilling: (runDate = '') => apiRequest('/billing/run/', { method: 'POST', body: { run_date: runDate } }),

  // Customers
  getCustomers: () => apiRequest('/customers/'),
  getCustomer: (uuid) => apiRequest(`/customers/${uuid}/`),
  createCustomer: (payload) => apiRequest('/customers/create/', { method: 'POST', body: payload }),

  // Catalogue
  getCatalogue: () => apiRequest('/catalogue/'),
  createPlan: (payload) => apiRequest('/plans/create/', { method: 'POST', body: payload }),

  // Proof Engine & Alerts
  getAlerts: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return apiRequest(`/alerts/${query ? `?${query}` : ''}`);
  },
  getAlert: (id) => apiRequest(`/alerts/${id}/`),
  applyAlertFix: (id) => apiRequest(`/alerts/${id}/fix/`, { method: 'POST' }),
  reviewAlert: (id, status, notes = '') => apiRequest(`/alerts/${id}/review/`, { method: 'POST', body: { status, notes } }),
  runDetection: (asOf = '') => apiRequest('/audit/run-detection/', { method: 'POST', body: { as_of: asOf } }),
  injectLeaks: () => apiRequest('/audit/leak-injection/', { method: 'POST' }),

  // Customer Portal
  getPortalData: () => apiRequest('/portal/'),
};

export function formatMoney(val) {
  if (val === null || val === undefined) return 'Rs. 0.00';
  const num = typeof val === 'number' ? val : parseFloat(val);
  return `Rs. ${num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export function formatDate(val) {
  if (!val) return '—';
  return val;
}
