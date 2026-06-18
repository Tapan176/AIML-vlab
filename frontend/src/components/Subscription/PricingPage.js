import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { useSubscription } from '../../context/SubscriptionContext';
import './Subscription.css';

function formatLimit(value) {
    if (value === null || value === undefined) return 'Unlimited';
    if (value === 0) return '—';
    return value;
}

// Display the canonical USD price formatted in the visitor's local currency.
// The CHARGE is still the canonical Stripe Price (Adaptive Pricing localizes
// the hosted checkout); this is purely cosmetic so the number shown matches the
// user's region. Price value is identical worldwide.
function makePriceFormatter(currency) {
    return (price) => {
        if (price === 0) return 'Free';
        try {
            const f = new Intl.NumberFormat(undefined, {
                style: 'currency', currency: currency || 'USD',
                maximumFractionDigits: 0,
            });
            return `${f.format(price)}/mo`;
        } catch (e) {
            return `$${price}/mo`;
        }
    };
}

export default function PricingPage() {
    const [plans, setPlans] = useState([]);
    const [loading, setLoading] = useState(true);
    const [paymentsEnabled, setPaymentsEnabled] = useState(false);
    const [provider, setProvider] = useState(null);
    const [currency, setCurrency] = useState('USD');
    const [error, setError] = useState(null);
    const { isAuthenticated } = useAuth();
    const { entitlements } = useSubscription();
    const navigate = useNavigate();
    const currentPlan = entitlements?.plan || 'free';
    const formatPrice = makePriceFormatter(currency);
    const providerLabel = provider === 'lemonsqueezy'
        ? 'Lemon Squeezy'
        : provider === 'stripe'
            ? 'Stripe'
            : 'our secure payment provider';

    useEffect(() => {
        let active = true;
        (async () => {
            try {
                const [data, locale] = await Promise.all([
                    api.get('/subscription/plans'),
                    api.get('/billing/locale').catch(() => null),
                ]);
                if (!active) return;
                setPlans((data && data.plans) || []);
                setPaymentsEnabled(!!(data && data.payments_enabled));
                setProvider((data && data.provider) || null);
                if (locale && locale.currency) setCurrency(locale.currency);
            } catch (e) {
                if (active) setPlans([]);
            } finally {
                if (active) setLoading(false);
            }
        })();
        return () => { active = false; };
    }, []);

    const handleSelectPlan = (planId) => {
        setError(null);
        if (planId === 'free' || planId === currentPlan) return;
        if (!isAuthenticated) {
            navigate(`/login?next=/checkout?plan=${planId}`);
            return;
        }
        // Go to the order/review page (shows the itemized bill before payment).
        navigate(`/checkout?plan=${planId}`);
    };

    const handleManageBilling = async () => {
        setError(null);
        try {
            const res = await api.post('/billing/portal', {});
            if (res && res.url) window.location.href = res.url;
        } catch (e) {
            setError(e?.message || 'Could not open billing portal.');
        }
    };

    return (
        <div className="pricing-page">
            <h1 className="pricing-heading">Plans &amp; Pricing</h1>
            <p className="pricing-subhead">
                Same price worldwide — shown in your local currency, billed securely via {providerLabel}.
            </p>
            {error && <p className="pricing-error">{error}</p>}

            {loading ? (
                <p className="pricing-loading">Loading plans…</p>
            ) : (
                <div className="pricing-grid">
                    {plans.map((plan) => {
                        const limits = plan.limits || {};
                        const popular = plan.id === 'pro';
                        const features = plan.features || [];
                        const isCurrent = plan.id === currentPlan;
                        const isPaid = plan.price > 0;
                        return (
                            <div
                                key={plan.id}
                                className={`plan-card${popular ? ' popular' : ''}${isCurrent ? ' current' : ''}`}
                            >
                                {popular && (
                                    <span className="plan-badge">Most popular</span>
                                )}
                                <h2 className="plan-name">{plan.name}</h2>
                                <div className="plan-price">
                                    {formatPrice(plan.price)}
                                </div>
                                {plan.blurb && (
                                    <p className="plan-blurb">{plan.blurb}</p>
                                )}

                                <ul className="plan-limits">
                                    <li>Classical: {formatLimit(limits.classical)}/mo</li>
                                    <li>Deep learning: {formatLimit(limits.deep)}/mo</li>
                                    <li>Fine-tuning: {formatLimit(limits.finetune)}/mo</li>
                                    <li>Data Studio: {formatLimit(limits.datastudio)}/mo</li>
                                    {plan.max_datasets != null && (
                                        <li>Datasets stored: {formatLimit(plan.max_datasets)}</li>
                                    )}
                                </ul>

                                {features.length > 0 && (
                                    <ul className="plan-features">
                                        {features.map((feature, idx) => (
                                            <li key={idx}>{feature.replace(/_/g, ' ')}</li>
                                        ))}
                                    </ul>
                                )}

                                {isCurrent ? (
                                    <button type="button" className="plan-cta current-cta" disabled>
                                        Current plan
                                    </button>
                                ) : isPaid ? (
                                    <button
                                        type="button"
                                        className="plan-cta"
                                        disabled={!paymentsEnabled}
                                        onClick={() => handleSelectPlan(plan.id)}
                                    >
                                        {!paymentsEnabled
                                            ? 'Coming soon'
                                            : `Upgrade to ${plan.name}`}
                                    </button>
                                ) : (
                                    <button type="button" className="plan-cta" disabled>
                                        {currentPlan === 'free' ? 'Current plan' : 'Free'}
                                    </button>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}

            {paymentsEnabled && currentPlan !== 'free' && (
                <div className="pricing-manage">
                    <button type="button" className="plan-cta secondary" onClick={handleManageBilling}>
                        Manage billing &amp; invoices
                    </button>
                </div>
            )}
        </div>
    );
}
