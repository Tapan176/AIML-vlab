import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import Pagination from '../shared/Pagination';
import './AdminDashboard.css';
import './Admin.css';

const LIMIT = 20;

const TYPE_OPTIONS = ['', 'bug', 'feature', 'general', 'other'];
const RESOLVED_OPTIONS = [
    { value: '', label: 'All' },
    { value: 'false', label: 'Unresolved' },
    { value: 'true', label: 'Resolved' },
];

export default function FeedbackInbox() {
    const { user } = useAuth();
    const [items, setItems] = useState([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [type, setType] = useState('');
    const [resolved, setResolved] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const totalPages = Math.max(1, Math.ceil(total / LIMIT));

    const fetchFeedback = useCallback(async () => {
        if (!user || user.role !== 'admin') return;
        setLoading(true);
        try {
            const params = new URLSearchParams({ page: String(page), limit: String(LIMIT) });
            if (type) params.set('type', type);
            if (resolved) params.set('resolved', resolved);
            const data = await api.get(`/admin/feedback?${params.toString()}`, { ttl: 0 });
            setItems(Array.isArray(data.feedback) ? data.feedback : []);
            setTotal(data.total || 0);
            setError(null);
        } catch (err) {
            setError(err.message || 'Failed to load feedback.');
        } finally {
            setLoading(false);
        }
    }, [user, page, type, resolved]);

    useEffect(() => {
        fetchFeedback();
    }, [fetchFeedback]);

    const handleToggleResolved = async (id, current) => {
        const next = !current;
        setItems((prev) => prev.map((f) => (f._id === id ? { ...f, resolved: next } : f)));
        try {
            await api.patch(`/admin/feedback/${id}`, { resolved: next });
        } catch (err) {
            setItems((prev) => prev.map((f) => (f._id === id ? { ...f, resolved: current } : f)));
            alert(err.message || 'Failed to update feedback.');
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm('Delete this feedback entry?')) return;
        try {
            await api.delete(`/admin/feedback/${id}`);
            fetchFeedback();
        } catch (err) {
            alert(err.message || 'Failed to delete feedback.');
        }
    };

    if (!user || user.role !== 'admin') {
        return (
            <div className="admin-denied">
                <h2>Access Denied</h2>
                <p>You do not have administrative privileges to view this page.</p>
            </div>
        );
    }

    return (
        <div className="admin-section">
            <h2>Feedback Inbox</h2>
            <div className="admin-toolbar">
                <select
                    value={type}
                    onChange={(e) => { setPage(1); setType(e.target.value); }}
                >
                    {TYPE_OPTIONS.map((t) => (
                        <option key={t || 'all'} value={t}>{t ? t : 'All types'}</option>
                    ))}
                </select>
                <select
                    value={resolved}
                    onChange={(e) => { setPage(1); setResolved(e.target.value); }}
                >
                    {RESOLVED_OPTIONS.map((opt) => (
                        <option key={opt.value || 'all'} value={opt.value}>{opt.label}</option>
                    ))}
                </select>
            </div>

            {error && <div className="admin-error-inline">{error}</div>}

            {loading ? (
                <p className="no-data">Loading feedback…</p>
            ) : items.length === 0 ? (
                <p className="no-data">No feedback found.</p>
            ) : (
                <div className="feedback-list">
                    {items.map((f) => (
                        <div className="feedback-card" key={f._id}>
                            <div className="feedback-card-head">
                                <span className="feedback-card-email">{f.email || 'Anonymous'}</span>
                                {f.type && <span className="badge badge-muted">{f.type}</span>}
                                <span className={`badge ${f.resolved ? 'badge-success' : 'badge-warning'}`}>
                                    {f.resolved ? 'Resolved' : 'Open'}
                                </span>
                                <span className="feedback-card-date">
                                    {f.created_at ? new Date(f.created_at).toLocaleDateString() : ''}
                                </span>
                            </div>
                            <div className="feedback-card-message">{f.message || ''}</div>
                            <div className="feedback-card-actions">
                                <button
                                    className="admin-btn-secondary"
                                    onClick={() => handleToggleResolved(f._id, !!f.resolved)}
                                >
                                    {f.resolved ? 'Mark unresolved' : 'Mark resolved'}
                                </button>
                                <button
                                    className="btn-danger-small"
                                    onClick={() => handleDelete(f._id)}
                                >
                                    Delete
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            <Pagination
                page={page}
                totalPages={totalPages}
                totalItems={total}
                pageSize={LIMIT}
                onChange={setPage}
                unitLabel="entries"
            />
        </div>
    );
}
