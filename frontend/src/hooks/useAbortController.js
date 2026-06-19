import { useEffect, useRef } from 'react';

/**
 * Cancels an in-flight fetch / SSE reader when the component unmounts (and when
 * a new run starts), so navigating away mid-training aborts the request instead
 * of leaving a detached `getReader()` loop running — wasted work plus setState
 * on an unmounted page.
 *
 * Returns a `nextSignal()` function: call it right before each fetch to abort
 * any previous run and get a fresh AbortSignal for the new one.
 *
 *   const nextSignal = useAbortController();
 *   const res = await fetch(url, { ..., signal: nextSignal() });
 *   ...
 *   } catch (err) { if (err.name !== 'AbortError') setError(err.message); }
 */
export default function useAbortController() {
    const ref = useRef(null);

    // Abort whatever is in flight when the page unmounts.
    useEffect(() => () => { if (ref.current) ref.current.abort(); }, []);

    return () => {
        if (ref.current) ref.current.abort();   // cancel any previous run
        ref.current = new AbortController();
        return ref.current.signal;
    };
}
