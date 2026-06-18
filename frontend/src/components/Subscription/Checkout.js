import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import './Subscription.css';

/**
 * Checkout / Order page.
 *
 * Shows a server-priced itemized BILL for the chosen plan before redirecting to
 * the payment provider's hosted checkout. The price + currency + provider come
 * from GET /billing/order, which resolves the buyer's region server-side (India
 * → Razorpay/₹, elsewhere → Lemon Squeezy/Stripe/$). On "Proceed to payment" we
 * call POST /billing/checkout and redirect to the returned hosted URL.
 *
 * Route: /checkout?plan=pro
 */
export default function Checkout() {
    const [params] = useSearchParams();
    const planId = params.get('plan');
    const navigate = useNavigate();
    const { isAuthenticated, user } = useAuth();

    const [order, setOrder] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [redirecting, setRedirecting] = useState(false);

    useEffect(() => {
        if (!isAuthenticated) {
            navigate(`/login?next=/checkout?plan=${planId}`);
            return;
        }
        if (!planId || planId === 'free') {
            navigate('/pricing');
            return;
        }
        let active = true;
        (async () => {
            try {
                const data = await api.post('/billing/order', { plan: planId });
                if (active) setOrder(data);
            } catch (e) {
                if (active) setError(e?.message || 'Could not load order.');
            } finally {
                if (active) setLoading(false);
            }
        })();
        return () => { active = false; };
    }, [planId, isAuthenticated, navigate]);

    const handlePay = async () => {
        setError(null);
        setRedirecting(true);
        try {
            const res = await api.post('/billing/checkout', { plan: planId });
            if (res && res.url) {
                window.location.href = res.url;
            } else {
                setError('Could not start checkout. Please try again.');
                setRedirecting(false);
            }
        } catch (e) {
            setError(e?.data?.error === 'payments_not_configured'
                ? 'Payments are not configured yet.'
                : (e?.message || 'Checkout failed.'));
            setRedirecting(false);
        }
    };

    if (loading) {
        return <div className="checkout-page"><p className="pricing-loading">Loading order…</p></div>;
    }

    return (
        <div className="checkout-page">
            <div className="checkout-card">
                <h1 className="checkout-title">Review your order</h1>
                <p className="checkout-sub">
                    Secure checkout via <strong>{order?.provider_label}</strong>
                    {order?.country === 'IN' ? ' (India)' : ''}
                </p>

                {error && <p className="pricing-error">{error}</p>}

                <div className="checkout-bill">
                    <div className="bill-row bill-header">
                        <span>Description</span>
                        <span>Amount</span>
                    </div>
                    {(order?.line_items || []).map((li, idx) => (
                        <div className="bill-row" key={idx}>
                            <span>{li.description}</span>
                            <span>{li.amount_display}</span>
                        </div>
                    ))}
                    <div className="bill-row bill-total">
                        <span>Total due today</span>
                        <span>{order?.total_display}</span>
                    </div>
                </div>

                {order?.tax_note && <p className="checkout-tax">{order.tax_note}</p>}

                <div className="checkout-billed-to">
                    <span className="muted">Billed to</span>
                    <span>{user?.email}</span>
                </div>

                {!order?.configured && (
                    <p className="pricing-error">
                        This payment method isn't configured yet. Please try again later.
                    </p>
                )}

                <button
                    type="button"
                    className="plan-cta checkout-pay-btn"
                    onClick={handlePay}
                    disabled={redirecting || !order?.configured}
                >
                    {redirecting ? 'Redirecting to secure payment…' : `Proceed to pay ${order?.total_display || ''}`}
                </button>

                <Link to="/pricing" className="checkout-back">← Back to plans</Link>

                <p className="checkout-fineprint">
                    You'll be redirected to {order?.provider_label} to complete payment securely.
                    We never see or store your card details. An invoice will be emailed to you
                    after a successful payment.
                </p>
            </div>
        </div>
    );
}
