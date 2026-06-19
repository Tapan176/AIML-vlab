import { useEffect, useRef, useState } from 'react';

/**
 * Throttle how often a rapidly-changing value is surfaced for render.
 *
 * Returns a copy of `value` that updates at most once per `delayMs`: the first
 * change commits immediately (leading edge), then at most one trailing commit
 * carries the latest value once the window elapses. Use it to cap expensive
 * redraws — e.g. the live <TrainingChart>, which would otherwise re-run recharts
 * on every per-epoch metric append (100 epochs → 100 redraws).
 *
 * The trailing commit guarantees the final value is always rendered, so the
 * chart settles on the complete dataset when a run finishes.
 */
export default function useThrottledValue(value, delayMs = 400) {
    const [throttled, setThrottled] = useState(value);
    // -Infinity → the very first change always commits immediately (leading).
    const lastCommitRef = useRef(-Infinity);
    const timerRef = useRef(null);
    const latestRef = useRef(value);
    latestRef.current = value;

    useEffect(() => {
        const now = Date.now();
        const elapsed = now - lastCommitRef.current;
        if (elapsed >= delayMs) {
            lastCommitRef.current = now;
            setThrottled(latestRef.current);
        } else if (timerRef.current == null) {
            timerRef.current = setTimeout(() => {
                lastCommitRef.current = Date.now();
                timerRef.current = null;
                setThrottled(latestRef.current);
            }, delayMs - elapsed);
        }
    }, [value, delayMs]);

    // Drop a pending trailing commit if we unmount mid-window.
    useEffect(() => () => {
        if (timerRef.current != null) clearTimeout(timerRef.current);
    }, []);

    return throttled;
}
