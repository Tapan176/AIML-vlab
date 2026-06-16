import { useState, useEffect } from 'react';
import api from '../../services/api';
import './Subscription.css';

function formatLimit(value) {
    if (value === null || value === undefined) return 'Unlimited';
    if (value === 0) return '—';
    return value;
}

function formatPrice(price) {
    if (price === 0) return 'Free';
    return `$${price}/mo`;
}

export default function PricingPage() {
    const [plans, setPlans] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let active = true;
        (async () => {
            try {
                const data = await api.get('/subscription/plans');
                if (active) setPlans((data && data.plans) || []);
            } catch (e) {
                if (active) setPlans([]);
            } finally {
                if (active) setLoading(false);
            }
        })();
        return () => { active = false; };
    }, []);

    return (
        <div className="pricing-page">
            <h1 className="pricing-heading">Plans &amp; Pricing</h1>

            {loading ? (
                <p className="pricing-loading">Loading plans…</p>
            ) : (
                <div className="pricing-grid">
                    {plans.map((plan) => {
                        const limits = plan.limits || {};
                        const popular = plan.id === 'pro';
                        const features = plan.features || [];
                        return (
                            <div
                                key={plan.id}
                                className={`plan-card${popular ? ' popular' : ''}`}
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
                                </ul>

                                {features.length > 0 && (
                                    <ul className="plan-features">
                                        {features.map((feature, idx) => (
                                            <li key={idx}>{feature}</li>
                                        ))}
                                    </ul>
                                )}

                                <button
                                    type="button"
                                    className="plan-cta"
                                    disabled
                                >
                                    Coming soon
                                </button>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
