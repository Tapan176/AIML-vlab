import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { useSubscription } from '../../context/SubscriptionContext';
import './Subscription.css';

/**
 * Manage Subscription — shown on the Profile page.
 *
 * Displays the user's current plan + status, lists their billing history
 * (invoices emailed after each successful payment), and offers actions:
 *   - Free user  → "Upgrade" (→ /pricing)
 *   - Paid user  → "Manage / Cancel" (POST /billing/portal). For Stripe/LS this
 *     opens the provider's hosted portal; for Razorpay it cancels at cycle end.
 *
 * Self-hides entirely when subscriptions are disabled (feature flag off).
 */
export default function ManageSubscription() {
    const { enabled, entitlements, refresh } = useSubscription();
    const navigate = useNavigate();
    const [invoices, setInvoices] = useState([]);
    const [busy, setBusy] = useState(false);
    const [msg, setMsg] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!enabled) return;
        let active = true;
        (async () => {
            try {
                const data = await api.get('/billing/invoices', { force: true });
                if (active) setInvoices((data && data.invoices) || []);
            } catch (e) {
                if (active) setInvoices([]);
            }
        })();
        return () => { active = false; };
    }, [enabled]);

    if (!enabled || !entitlements) return null;

    const plan = entitlements.plan || 'free';
    const planName = entitlements.plan_name || 'Free';
    const isPaid = plan !== 'free';

    const handleManage = async () => {
        setError(null);
        setMsg(null);
        if (!isPaid) {
            navigate('/pricing');
            return;
        }
        setBusy(true);
        try {
            const res = await api.post('/billing/portal', {});
            if (res && res.url) {
                window.location.href = res.url; // Stripe/LS hosted portal
            } else if (res && res.cancelled) {
                setMsg(res.message || 'Your subscription will end at the current cycle.');
                refresh?.();
            } else {
                setError('Could not open billing management.');
            }
        } catch (e) {
            setError(e?.message === 'no_active_subscription'
                ? 'No active subscription to manage.'
                : (e?.message || 'Could not open billing management.'));
        } finally {
            setBusy(false);
        }
    };

    return (
        <div className="billing-section">
            <h2>Subscription &amp; billing</h2>

            <div className="billing-plan-row">
                <div>
                    <span className="billing-plan-name">{planName} plan</span>
                    {isPaid && <span className="billing-status">Active</span>}
                </div>
                <div className="billing-actions">
                    {isPaid ? (
                        <>
                            <button
                                type="button"
                                className="billing-btn"
                                onClick={handleManage}
                                disabled={busy}
                            >
                                {busy ? 'Working…' : 'Manage / Cancel'}
                            </button>
                            <button
                                type="button"
                                className="billing-btn primary"
                                onClick={() => navigate('/pricing')}
                            >
                                Change plan
                            </button>
                        </>
                    ) : (
                        <button
                            type="button"
                            className="billing-btn primary"
                            onClick={() => navigate('/pricing')}
                        >
                            Upgrade plan
                        </button>
                    )}
                </div>
            </div>

            {msg && <p className="auth-info">{msg}</p>}
            {error && <p className="pricing-error">{error}</p>}

            <h2 style={{ fontSize: '1rem', marginTop: '0.5rem' }}>Billing history</h2>
            {invoices.length === 0 ? (
                <p className="invoice-empty">No invoices yet. Your invoices will appear here after a payment.</p>
            ) : (
                <ul className="invoice-list">
                    {invoices.map((inv) => (
                        <li className="invoice-row" key={inv.id || inv.invoice_number}>
                            <div className="invoice-meta">
                                <span className="invoice-num">{inv.invoice_number}</span>
                                <span className="invoice-date">{inv.date} · {inv.plan_name} · {inv.provider_label}</span>
                            </div>
                            <span>{inv.total_display || inv.amount_display}</span>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}
