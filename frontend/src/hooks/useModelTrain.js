import { useState, useCallback } from 'react';
import api from '../services/api';
import { API_URL } from '../constants';

/**
 * Hook encapsulating the train-and-render pattern used by every Model page:
 * POST a body to a model endpoint, manage loading/error/results state, and
 * normalise the response so consumers can iterate `results.images` regardless
 * of whether the backend returned base64 payloads or URL pointers.
 */
export default function useModelTrain(endpoint, options = {}) {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [results, setResults] = useState(null);

    const train = useCallback(async (body) => {
        setLoading(true);
        setError('');
        try {
            const data = await api.post(endpoint, body);
            // Why: backend may return either inline base64 (newer models) or
            // URL pointers that need the API base prefix + cache-buster.
            const images = data?.outputImageBase64?.length > 0
                ? data.outputImageBase64
                : (data?.outputImageUrls?.map(u => `${API_URL}/${u}?timestamp=${Date.now()}`) || []);
            const normalised = { ...data, images };
            setResults(normalised);
            // Tell the subscription usage widget to refresh (a run was recorded).
            try { window.dispatchEvent(new CustomEvent('aiml:trained')); } catch (e) {}
            return normalised;
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setLoading(false);
        }
    }, [endpoint]);

    const reset = useCallback(() => {
        setResults(null);
        setError('');
        setLoading(false);
    }, []);

    return { train, loading, error, results, reset };
}
