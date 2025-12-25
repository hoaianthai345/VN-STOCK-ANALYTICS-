import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000/api/v1', // Adjust if backend runs on different port
});

export const getMarketSummary = () => api.get('/market/summary');
export const getBankHistory = (symbol) => api.get(`/market/history/${symbol}`);
export const getSymbols = () => api.get('/market/symbols');
export const getBankFinancials = (symbol) => api.get(`/market/financials/${symbol}`);
export const consultAdvisor = (data) => api.post('/advisor/consult', data);
export const getLogs = () => api.get('/admin/logs');
export const triggerPipeline = () => api.post('/admin/trigger-pipeline');
export const retrainModel = () => api.post('/admin/retrain-model');
export const getTrainingResults = () => api.get('/admin/training-results');
export const getTrainingMetrics = () => api.get('/admin/training-metrics');

export default api;
