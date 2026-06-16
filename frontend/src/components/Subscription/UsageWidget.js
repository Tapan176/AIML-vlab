import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useSubscription } from '../../context/SubscriptionContext';
import './Subscription.css';

const RUN_CLASSES = [
    { key: 'classical', label: 'Classical ML' },
    { key: 'deep', label: 'Deep Learning' },
    { key: 'finetune', label: 'Fine-Tuning' },
    { key: 'datastudio', label: 'Data Studio' }
];

function formatDate(value) {
    if (!value) return null;
    const d = new Date(value);
    if (isNaN(d.getTime())) return null;
    return d.toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

export default function UsageWidget() {
    const { enabled, entitlements, refresh } = useSubscription();

    // Pull fresh usage every time the widget mounts (e.g. landing on the
    // Dashboard right after a training run on a model page) so the counts are
    // current. Hooks must run before any early return.
    useEffect(() => {
        if (enabled && refresh) refresh();
    }, [enabled, refresh]);

    if (!enabled || !entitlements) return null;

    const limits = entitlements.limits || {};
    const usage = entitlements.usage || {};
    const planName = entitlements.plan_name || entitlements.plan || 'Free';
    const resetDate = formatDate(entitlements.reset_at);
    const datasetsUsed = usage.datasets;

    return (
        <div className="usage-widget">
            <div className="usage-header">
                <h3 className="usage-title">Your Usage — {planName} plan</h3>
                <Link to="/pricing" className="usage-upgrade">Upgrade</Link>
            </div>
            {resetDate && (
                <p className="usage-reset">Resets {resetDate}</p>
            )}

            {RUN_CLASSES.map(({ key, label }) => {
                const used = usage[key] || 0;
                const limit = limits[key];
                const unlimited = limit === null || limit === undefined;
                const atLimit = !unlimited && used >= limit;
                const pct = unlimited
                    ? 0
                    : Math.min(100, limit > 0 ? (used / limit) * 100 : 100);

                return (
                    <div className="usage-row" key={key}>
                        <div className="usage-row-head">
                            <span className="usage-label">{label}</span>
                            <span className="usage-count">
                                {unlimited
                                    ? `${used} / Unlimited`
                                    : `${used} / ${limit}`}
                            </span>
                        </div>
                        {!unlimited && (
                            <div className="usage-bar">
                                <div
                                    className="usage-bar-fill"
                                    style={{
                                        width: `${pct}%`,
                                        background: atLimit
                                            ? 'var(--danger)'
                                            : 'var(--accent)'
                                    }}
                                />
                            </div>
                        )}
                    </div>
                );
            })}

            {datasetsUsed != null && (
                <div className="usage-row">
                    <div className="usage-row-head">
                        <span className="usage-label">Datasets stored</span>
                        <span className="usage-count">{datasetsUsed}</span>
                    </div>
                </div>
            )}
        </div>
    );
}
