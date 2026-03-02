import axios from 'axios';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
    headers: {
        'Content-Type': 'application/json',
    },
});

export const entries = {
    upload: (formData) => api.post('/entries/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    }),
    getAll: (params) => api.get('/entries', { params }),
    getById: (id) => api.get(`/entries/${id}`),
    update: (id, data) => api.patch(`/entries/${id}`, data),
    delete: (id) => api.delete(`/entries/${id}`),
};

export const pipeline = {
    getStatus: (taskId) => api.get(`/pipeline/status/${taskId}`),
    getLogs: (entryId) => api.get(`/pipeline/logs/${entryId}`),
};

export const tags = {
    getAll: () => api.get('/tags'),
    create: (data) => api.post('/tags', data),
    update: (id, data) => api.patch(`/tags/${id}`, data),
    delete: (id) => api.delete(`/tags/${id}`),
};

export const profile = {
    get: () => api.get('/profile'),
    update: (data) => api.put('/profile', data),
};

export const config = {
    getModels: () => api.get('/config/models'),
    updateModel: (id, data) => api.put(`/config/models/${id}`, data),
};

export const stats = {
    get: () => api.get('/stats'),
};

export default api;
