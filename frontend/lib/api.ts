import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Dashboard
export const getDashboardSummary = () => api.get('/dashboard/summary');
export const getDashboardFunnel = () => api.get('/dashboard/funnel');
export const getDashboardFailures = () => api.get('/dashboard/failures');

// Payments
export const listPayments = (params?: any) => api.get('/payments', { params });
export const getPayment = (id: number) => api.get(`/payments/${id}`);

// Recovery
export const listRecoveryCases = (params?: any) => api.get('/recovery/cases', { params });
export const getRecoveryCase = (id: number) => api.get(`/recovery/cases/${id}`);
export const analyzeCase = (id: number) => api.post(`/recovery/cases/${id}/analyze`);
export const executeCase = (id: number) => api.post(`/recovery/cases/${id}/execute`);
export const escalateCase = (id: number) => api.post(`/recovery/cases/${id}/escalate`);

// Audit
export const listAuditLogs = (params?: any) => api.get('/audit', { params });
export const getEntityLogs = (entityId: number, entityType: string) =>
  api.get(`/audit/${entityId}`, { params: { entity_type: entityType } });

// Policies
export const getPolicies = () => api.get('/policies');
export const updatePolicies = (data: any) => api.put('/policies', data);

// Health
export const getHealth = () => api.get('/health');
