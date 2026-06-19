import { useCallback, useRef, useState } from 'react';
import api from '../services/api';
import { API_URL } from '../constants';
import pollSessionProgress from '../utils/pollSessionProgress';

/**
 * Hook encapsulating the train-and-render pattern used by every Model page:
 * POST a body to a model endpoint, manage loading/error/results state, and
 * normalise the response so consumers can iterate `results.images` regardless
 * of whether the backend returned base64 payloads or URL pointers.
 *
 * Async-aware: when TRAINING_ASYNC is enabled the backend enqueues the run and
 * responds 202 { session_id, status: 'queued' } instead of blocking. In that
 * case this hook transparently polls /training-sessions/<id>/progress until the
 * run finishes and resolves with the same normalised shape, so callers don't
 * need to know whether training ran sync or async. `progress` exposes the live
 * status/logs while a queued run is in flight.
 */
export default function useModelTrain(endpoint, options = {}) {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [results, setResults] = useState(null);
    const [progress, setProgress] = useState(null);  // { status, logs, metrics } while queued
    const cancelledRef = useRef(false);

    const normalise = (data) => {
        // Backend may return inline base64 (newer models) or URL pointers that
        // need the API base prefix + cache-buster.
        const images = data?.outputImageBase64?.length > 0
            ? data.outputImageBase64
            : (data?.outputImageUrls?.map(u => `${API_URL}/${u}?timestamp=${Date.now()}`) || []);
        return { ...data, images };
    };

    const train = useCallback(async (body) => {
        cancelledRef.current = false;
        setLoading(true);
        setError('');
        setProgress(null);
        try {
            const data = await api.post(endpoint, body);

            // Async path: the run was queued. Poll for the outcome and resolve
            // with the completed results (same shape as the sync response).
            if (data && data.status === 'queued' && data.session_id) {
                setProgress({ status: 'queued', logs: [], metrics: [] });
                const finalData = await pollSessionProgress(api, data.session_id, {
                    isCancelled: () => cancelledRef.current,
                    onProgress: (snap) => setProgress(snap),
                });
                const normalised = normalise(finalData);
                setResults(normalised);
                setProgress(null);
                try { window.dispatchEvent(new CustomEvent('aiml:trained')); } catch (e) {}
                return normalised;
            }

            // Sync path: results are inline in the response.
            const normalised = normalise(data);
            setResults(normalised);
            // Tell the subscription usage widget to refresh (a run was recorded).
            try { window.dispatchEvent(new CustomEvent('aiml:trained')); } catch (e) {}
            return normalised;
        } catch (err) {
            if (!err.cancelled) setError(err.message);
            throw err;
        } finally {
            setLoading(false);
        }
    }, [endpoint]);

    const reset = useCallback(() => {
        cancelledRef.current = true;
        setResults(null);
        setError('');
        setProgress(null);
        setLoading(false);
    }, []);

    return { train, loading, error, results, progress, reset };
}
