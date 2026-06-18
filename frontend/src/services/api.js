/**
 * Centralized API service with JWT authentication.
 * All API calls should use these helpers.
 *
 * GET requests are de-duplicated and briefly cached:
 *   - _inflight collapses concurrent identical GETs into a single network
 *     request — this is what eliminates the React 18 StrictMode "double fetch"
 *     in dev (both mounts await the same promise) AND same-page duplicate calls
 *     from two components hitting the same endpoint.
 *   - _cache serves a short-TTL copy so rapid repeat navigation between pages
 *     doesn't re-hit the network for unchanged lists.
 * Any write (post/put/upload/delete) clears the GET cache so stale lists are
 * never served after a mutation. Call clearCache() on logout.
 */

import { API_URL, TOKEN_KEY } from '../constants';

const API_BASE = API_URL;

function getToken() {
    return localStorage.getItem(TOKEN_KEY);
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

// --- GET de-dup + cache ---------------------------------------------------
const _inflight = new Map();   // key -> Promise (dedupes concurrent GETs)
const _cache = new Map();      // key -> { data, expires }
const DEFAULT_TTL = 30000;     // 30s

function _now() {
    // Date.now via a function so it's easy to reason about / stub.
    return new Date().getTime();
}

function _clone(data) {
    // Return a copy so callers that mutate results can't poison the cache.
    if (data == null || typeof data !== 'object') return data;
    try {
        return JSON.parse(JSON.stringify(data));
    } catch (e) {
        return data;
    }
}

/** Drop cached GET responses. Pass a prefix to clear a subset, or nothing to clear all. */
export function clearCache(prefix) {
    if (!prefix) {
        _cache.clear();
        return;
    }
    for (const key of _cache.keys()) {
        if (key.includes(prefix)) _cache.delete(key);
    }
}

async function parseBody(res) {
    // Read as text first so we can gracefully handle invalid JSON (e.g., NaN from backend)
    const text = await res.text();
    try {
        return text ? JSON.parse(text) : {};
    } catch (e) {
        // Fallback: sanitize common non‑JSON tokens like NaN/Infinity and retry
        const sanitized = text
            .replace(/\bNaN\b/g, 'null')
            .replace(/\bInfinity\b/g, 'null')
            .replace(/\b-Infinity\b/g, 'null');
        return sanitized ? JSON.parse(sanitized) : {};
    }
}

async function handleResponse(res) {
    const data = await parseBody(res);
    if (res.status === 401) {
        // Token expired — clear and redirect
        localStorage.removeItem(TOKEN_KEY);
        clearCache();
        window.location.href = '/login';
        throw new Error('Session expired');
    }
    if (!res.ok) {
        // Subscription quota hit — broadcast so a global upgrade modal can show.
        // Covers both monthly run quotas and the per-account storage (dataset)
        // cap so users get the friendly upgrade prompt instead of a raw error.
        if (res.status === 429 && data &&
            (data.error === 'quota_exceeded' || data.error === 'storage_quota_exceeded')) {
            try {
                window.dispatchEvent(new CustomEvent('aiml:quota', { detail: data }));
            } catch (e) { /* non-browser env */ }
        }
        // Prefer a human-readable `message` (quota errors set it) over the
        // machine `error` code.
        const err = new Error(data.message || data.error || `Request failed (${res.status})`);
        err.status = res.status;
        err.data = data;
        throw err;
    }
    return data;
}

export const api = {
    get: async (endpoint, { ttl = DEFAULT_TTL, force = false } = {}) => {
        const key = `GET ${endpoint}`;

        // `force` bypasses the cached value, but we still join any in-flight
        // identical request so StrictMode's double mount collapses to one call.
        if (!force) {
            const hit = _cache.get(key);
            if (hit && hit.expires > _now()) return _clone(hit.data);
        }
        if (_inflight.has(key)) return _inflight.get(key).then(_clone);

        const p = fetch(`${API_BASE}${endpoint}`, { headers: getHeaders() })
            .then(handleResponse)
            .then(data => {
                if (ttl > 0) _cache.set(key, { data, expires: _now() + ttl });
                return data;
            })
            .finally(() => { _inflight.delete(key); });

        _inflight.set(key, p);
        // Don't cache rejections — a retry should re-fetch.
        return p.then(_clone).catch(err => { _cache.delete(key); throw err; });
    },

    // Authenticated GET that does NOT hard-redirect on 401 — used during silent
    // session rehydrate (AuthContext) where a bad/expired token should just
    // resolve to "not logged in" rather than bounce to /login. Shares the same
    // in-flight dedup so StrictMode's double mount fires one /me request.
    authGet: async (endpoint, token, { ttl = 5000, force = false } = {}) => {
        const key = `AUTHGET ${endpoint}`;
        if (!force) {
            const hit = _cache.get(key);
            if (hit && hit.expires > _now()) return _clone(hit.data);
        }
        if (_inflight.has(key)) return _inflight.get(key).then(_clone);
        const headers = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = `Bearer ${token}`;
        const p = fetch(`${API_BASE}${endpoint}`, { headers })
            .then(async res => {
                const data = await parseBody(res);
                if (!res.ok) {
                    const err = new Error(data.error || `Request failed (${res.status})`);
                    err.status = res.status;
                    throw err;
                }
                if (ttl > 0) _cache.set(key, { data, expires: _now() + ttl });
                return data;
            })
            .finally(() => { _inflight.delete(key); });
        _inflight.set(key, p);
        return p.then(_clone).catch(err => { _cache.delete(key); throw err; });
    },

    post: async (endpoint, body) => {
        const res = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify(body)
        });
        const data = await handleResponse(res);
        clearCache();
        return data;
    },

    put: async (endpoint, body) => {
        const res = await fetch(`${API_BASE}${endpoint}`, {
            method: 'PUT',
            headers: getHeaders(),
            body: JSON.stringify(body)
        });
        const data = await handleResponse(res);
        clearCache();
        return data;
    },

    patch: async (endpoint, body) => {
        const res = await fetch(`${API_BASE}${endpoint}`, {
            method: 'PATCH',
            headers: getHeaders(),
            body: JSON.stringify(body)
        });
        const data = await handleResponse(res);
        clearCache();
        return data;
    },

    upload: async (endpoint, formData) => {
        const res = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers: getHeaders(true, false),
            body: formData
        });
        const data = await handleResponse(res);
        clearCache();
        return data;
    },

    // Unprotected post (for login/signup)
    publicPost: async (endpoint, body) => {
        const res = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers: getHeaders(false),
            body: JSON.stringify(body)
        });
        return handleResponse(res);
    },

    delete: async (endpoint) => {
        const res = await fetch(`${API_BASE}${endpoint}`, {
            method: 'DELETE',
            headers: getHeaders()
        });
        const data = await handleResponse(res);
        clearCache();
        return data;
    }
};

export default api;
