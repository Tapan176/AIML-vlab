import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import { useAuth } from './AuthContext';

/**
 * Tracks the signed-in user's in-flight training runs so a global navbar badge
 * can tell them a run continues after they navigate away from its page.
 *
 * Source of truth is the persisted session (GET /training-sessions/active), so
 * it survives reloads and even reflects runs started in another tab. Kept fresh
 * by a light poll (paused while the tab is hidden) plus an immediate refresh on
 * the aiml:trained / aiml:training-started events so the badge appears/clears
 * promptly without a tight interval.
 */
const TrainingContext = createContext({ activeRuns: [], count: 0, refresh: () => {} });

export const useTraining = () => useContext(TrainingContext);

const POLL_MS = 15000;

export function TrainingProvider({ children }) {
    const { isAuthenticated } = useAuth();
    const [activeRuns, setActiveRuns] = useState([]);

    const refresh = useCallback(async () => {
        if (!isAuthenticated) {
            setActiveRuns([]);
            return;
        }
        try {
            const data = await api.get('/training-sessions/active', { ttl: 0, force: true });
            setActiveRuns(Array.isArray(data?.active) ? data.active : []);
        } catch (_) {
            // Transient error — keep the last known state rather than flicker.
        }
    }, [isAuthenticated]);

    useEffect(() => {
        if (!isAuthenticated) {
            setActiveRuns([]);
            return undefined;
        }
        refresh();
        const id = setInterval(() => { if (!document.hidden) refresh(); }, POLL_MS);
        const onChange = () => refresh();
        const onVisible = () => { if (!document.hidden) refresh(); };
        window.addEventListener('aiml:trained', onChange);
        window.addEventListener('aiml:training-started', onChange);
        document.addEventListener('visibilitychange', onVisible);
        return () => {
            clearInterval(id);
            window.removeEventListener('aiml:trained', onChange);
            window.removeEventListener('aiml:training-started', onChange);
            document.removeEventListener('visibilitychange', onVisible);
        };
    }, [isAuthenticated, refresh]);

    return (
        <TrainingContext.Provider value={{ activeRuns, count: activeRuns.length, refresh }}>
            {children}
        </TrainingContext.Provider>
    );
}

export default TrainingContext;
