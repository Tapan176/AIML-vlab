/**
 * Single source of truth for model metadata on the frontend.
 *
 * Fetches /models/registry (backed by backend/services/model_registry.py) once
 * per SPA lifetime and caches it at module scope. The registry carries each
 * model's category, icon, file_extension, endpoint and streaming flag — so the
 * Sidebar, Dashboard, etc. derive their UI from it instead of re-hardcoding the
 * same lists. Add a model to the backend registry and it shows up everywhere.
 *
 * If the fetch fails (offline / cold start) we fall back to the static
 * MODEL_CATEGORIES + CATEGORY_ICONS in constants so the UI still renders.
 */
import { useState, useEffect } from 'react';
import { API_URL, MODEL_CATEGORIES, CATEGORY_ICONS } from '../constants';

let _cache = null;     // resolved registry object
let _promise = null;   // in-flight fetch (dedupes concurrent mounts)

const prettify = (code) =>
    code.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');

// Build a registry-shaped object from the static constants. file_extension
// can't be known here, so default to '.pkl' (only used for the download
// filename hint; the session download route uses the stored filename anyway).
function buildFallback() {
    const models = {};
    const categories = {};
    for (const [cat, codes] of Object.entries(MODEL_CATEGORIES)) {
        categories[cat] = { name: cat, icon: CATEGORY_ICONS[cat] || '📦', models: [...codes] };
        codes.forEach(code => {
            models[code] = {
                code,
                name: prettify(code),
                category: cat,
                icon: CATEGORY_ICONS[cat] || '📦',
                file_extension: '.pkl',
            };
        });
    }
    return { models, categories, total: Object.keys(models).length, _fallback: true };
}

export function fetchModelRegistry() {
    if (_cache) return Promise.resolve(_cache);
    if (_promise) return _promise;
    _promise = fetch(`${API_URL}/models/registry`)
        .then(res => {
            if (!res.ok) throw new Error(`registry ${res.status}`);
            return res.json();
        })
        .then(data => {
            if (!data || !data.models || !data.categories) throw new Error('bad registry shape');
            _cache = data;
            return data;
        })
        .catch(() => {
            _promise = null;           // allow a retry on the next mount
            return buildFallback();    // never let the UI break on a registry miss
        });
    return _promise;
}

/** React hook: returns the registry once loaded, or null on the first render. */
export function useModelRegistry() {
    const [registry, setRegistry] = useState(_cache);
    useEffect(() => {
        let active = true;
        fetchModelRegistry().then(r => { if (active) setRegistry(r); });
        return () => { active = false; };
    }, []);
    return registry;
}

/** Resolve a model's artifact extension from the registry, defaulting to .pkl. */
export function getModelExtension(registry, modelCode) {
    return registry?.models?.[modelCode]?.file_extension || '.pkl';
}
