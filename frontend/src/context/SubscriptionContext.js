import {
    createContext,
    useContext,
    useState,
    useEffect,
    useCallback
} from 'react';
import api from '../services/api';
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
        if (!localStorage.getItem('aiml_token')) return;
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
