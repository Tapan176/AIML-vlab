import { Link } from 'react-router-dom';
import './Subscription.css';

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

export default function UpgradeModal({ info, onClose }) {
    const resetDate = info ? formatDate(info.reset_at) : null;
    const isStorage = info && info.error === 'storage_quota_exceeded';
    const title = isStorage ? 'Storage limit reached' : 'Usage limit reached';

    return (
        <div className="upgrade-overlay" onClick={onClose}>
            <div
                className="upgrade-card"
                role="dialog"
                aria-modal="true"
                onClick={(e) => e.stopPropagation()}
            >
                <h2 className="upgrade-title">{title}</h2>
                {info && info.message && (
                    <p className="upgrade-message">{info.message}</p>
                )}
                {resetDate && (
                    <p className="upgrade-reset">Resets on {resetDate}</p>
                )}
                <div className="upgrade-actions">
                    <Link
                        to="/pricing"
                        className="upgrade-btn upgrade-btn-primary"
                        onClick={onClose}
                    >
                        View plans
                    </Link>
                    <button
                        type="button"
                        className="upgrade-btn upgrade-btn-secondary"
                        onClick={onClose}
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
}
