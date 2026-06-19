/**
 * Persists a model page's hyperparameter form across remounts and page
 * refreshes via localStorage under the key `${modelCode}_hyperparams`.
 *
 * Mirrors useDatasetCache: the lab now keeps the *selected model* in the URL
 * (/lab/:modelCode) and the *dataset* + *hyperparams* in localStorage, so an
 * accidental refresh no longer wipes a half-configured run.
 *
 * Seeding precedence on mount:
 *   1. `seed` (e.g. replayed session hyperparams) — an explicit request wins.
 *   2. cached values in localStorage — restores an in-progress edit.
 *   3. {} — fresh start; HyperparamPanel fills in schema defaults.
 *
 * Returns [hyperparams, setHyperparams] with the same shape as useState, so a
 * component can swap `useState(replayHyperparams)` for
 * `useHyperparamCache(MODEL_CODE, replayHyperparams)` with no other changes.
 */
import { useCallback, useEffect, useRef, useState } from 'react';

function cacheKey(modelCode) {
    return `${modelCode}_hyperparams`;
}

function readCache(modelCode) {
    try {
        const raw = localStorage.getItem(cacheKey(modelCode));
        if (!raw) return null;
        const parsed = JSON.parse(raw);
        return parsed && typeof parsed === 'object' ? parsed : null;
    } catch (e) {
        return null;
    }
}

export default function useHyperparamCache(modelCode, seed) {
    // Capture the seed once (replay payloads are one-shot). A non-empty seed
    // takes precedence over the cache; otherwise fall back to whatever the user
    // last had open for this model.
    const [hyperparams, setHyperparamsState] = useState(() => {
        if (seed && Object.keys(seed).length > 0) return seed;
        return readCache(modelCode) || {};
    });

    // Skip persisting the very first render so an empty initial form doesn't
    // clobber a freshly-seeded cache before HyperparamPanel has filled defaults.
    const firstRun = useRef(true);
    const writeTimerRef = useRef(null);
    const latestRef = useRef(hyperparams);
    latestRef.current = hyperparams;

    const persist = useCallback((val) => {
        try {
            if (val && Object.keys(val).length > 0) {
                localStorage.setItem(cacheKey(modelCode), JSON.stringify(val));
            }
        } catch (e) {
            // Storage full / disabled — non-fatal; form still works in-memory.
        }
    }, [modelCode]);

    useEffect(() => {
        if (firstRun.current) {
            firstRun.current = false;
            // Still persist a non-empty seed so a refresh right after replay keeps it.
            if (seed && Object.keys(seed).length > 0) persist(seed);
            return;
        }
        // Debounce: number inputs fire onChange on every keystroke; coalesce the
        // writes so a burst of edits hits localStorage once, not on every key.
        if (writeTimerRef.current) clearTimeout(writeTimerRef.current);
        writeTimerRef.current = setTimeout(() => {
            persist(latestRef.current);
            writeTimerRef.current = null;
        }, 300);
    }, [hyperparams, modelCode, seed, persist]);

    // Flush a pending write on unmount so an edit made <300ms before navigating
    // away (SPA route change) isn't lost.
    useEffect(() => () => {
        if (writeTimerRef.current) {
            clearTimeout(writeTimerRef.current);
            persist(latestRef.current);
        }
    }, [persist]);

    // Accepts either a value or an updater fn, like useState's setter.
    const setHyperparams = useCallback((next) => {
        setHyperparamsState(next);
    }, []);

    return [hyperparams, setHyperparams];
}
