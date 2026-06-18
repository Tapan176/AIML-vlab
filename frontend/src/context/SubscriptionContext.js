import {
    createContext,
    useContext,
    useState,
    useEffect,
    useCallback
} from 'react';
import api from '../services/api';
import { TOKEN_KEY } from '../constants';
import UpgradeModal from '../components/Subscription/UpgradeModal';

const SubscriptionContext = createContext(null);

export const useSubscription = () => useContext(SubscriptionContext);

export const SubscriptionProvider = ({ children }) => {
    const [enabled, setEnabled] = useState(false);
    const [entitlements, setEntitlements] = useState(null);
    const [quotaInfo, setQuotaInfo] = useState(null);

    // Fetch the public feature flag once on mount.
    useEffect(() => {
        let active = true;
        (async () => {
            try {
                const data = await api.get('/config');
                if (active) setEnabled(!!(data && data.subscription_enabled));
            } catch (e) {
                if (active) setEnabled(false);
            }
        })();
        return () => { active = false; };
    }, []);

    // Pull the current user's entitlements/usage. Only safe when the feature is
    // on AND a token exists (a 401 from api.get hard-redirects to /login).
    const refresh = useCallback(async () => {
        if (!enabled) return;
        if (!localStorage.getItem(TOKEN_KEY)) return;
        try {
            const data = await api.get('/subscription/me', { force: true });
            setEntitlements(data);
        } catch (e) {
            // Swallow — entitlements stay as-is / null.
        }
    }, [enabled]);

    // Load entitlements whenever the feature becomes enabled.
    useEffect(() => {
        if (enabled) refresh();
    }, [enabled, refresh]);

    // Listen for quota-exceeded events broadcast by the API client.
    useEffect(() => {
        const handler = (e) => setQuotaInfo(e.detail);
        window.addEventListener('aiml:quota', handler);
        return () => window.removeEventListener('aiml:quota', handler);
    }, []);

    // Refresh usage in (near) real time whenever a training run is kicked off
    // or completes (model pages dispatch 'aiml:trained'), AND whenever a usage
    // event explicitly asks for it ('aiml:usage'). The server increments the
    // counter at session creation, so this reflects the new run immediately.
    useEffect(() => {
        const handler = () => refresh();
        window.addEventListener('aiml:trained', handler);
        window.addEventListener('aiml:usage', handler);
        return () => {
            window.removeEventListener('aiml:trained', handler);
            window.removeEventListener('aiml:usage', handler);
        };
    }, [refresh]);

    // Refresh when the tab regains focus / becomes visible, so usage is current
    // after the user trains in one place and switches to the Profile page.
    useEffect(() => {
        if (!enabled) return undefined;
        const onFocus = () => refresh();
        const onVisible = () => { if (document.visibilityState === 'visible') refresh(); };
        window.addEventListener('focus', onFocus);
        document.addEventListener('visibilitychange', onVisible);
        return () => {
            window.removeEventListener('focus', onFocus);
            document.removeEventListener('visibilitychange', onVisible);
        };
    }, [enabled, refresh]);

    const value = { enabled, entitlements, refresh };

    return (
        <SubscriptionContext.Provider value={value}>
            {children}
            {quotaInfo && (
                <UpgradeModal info={quotaInfo} onClose={() => setQuotaInfo(null)} />
            )}
        </SubscriptionContext.Provider>
    );
};

export default SubscriptionProvider;
