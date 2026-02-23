/**
 * Centralized API service with JWT authentication.
 * All API calls should use these helpers.
 */

import { API_URL } from '../constants';

const API_BASE = API_URL;

function getToken() {
    return localStorage.getItem('aiml_token');
}

function getHeaders(includeAuth = true, isJson = true) {
    const headers = {};
    if (isJson) headers['Content-Type'] = 'application/json';
    if (includeAuth) {
        const token = getToken();
        if (token) headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
}

async function handleResponse(res) {
    const data = await res.json();
    if (res.status === 401) {
        // Token expired — clear and redirect
        localStorage.removeItem('aiml_token');
        window.location.href = '/login';
        throw new Error('Session expired');
    }
    if (!res.ok) {
        throw new Error(data.error || `Request failed (${res.status})`);
    }
    return data;
}

export const api = {
    get: async (endpoint) => {
        const res = await fetch(`${API_BASE}${endpoint}`, {
            headers: getHeaders()
        });
        return handleResponse(res);
    },

    post: async (endpoint, body) => {
        const res = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify(body)
        });
        return handleResponse(res);
    },

    put: async (endpoint, body) => {
        const res = await fetch(`${API_BASE}${endpoint}`, {
            method: 'PUT',
            headers: getHeaders(),
            body: JSON.stringify(body)
        });
        return handleResponse(res);
    },

    upload: async (endpoint, formData) => {
        const res = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers: getHeaders(true, false),
            body: formData
        });
        return handleResponse(res);
    },

    // Unprotected post (for login/signup)
    publicPost: async (endpoint, body) => {
        const res = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers: getHeaders(false),
            body: JSON.stringify(body)
        });
        return handleResponse(res);
    }
};

export default api;
