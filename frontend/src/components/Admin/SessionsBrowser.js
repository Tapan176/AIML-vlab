import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useUI } from '../../context/UIDialog';
import { MODEL_CATEGORIES } from '../../constants';
import api from '../../services/api';
import Pagination from '../shared/Pagination';
import './AdminDashboard.css';
import './Admin.css';

const LIMIT = 20;

const STATUS_OPTIONS = ['', 'pending', 'running', 'completed', 'failed'];

// Flatten MODEL_CATEGORIES into a sorted, de-duped list of model codes.
const MODEL_CODES = Array.from(
    new Set(Object.values(MODEL_CATEGORIES || {}).flat())
).sort();

function statusBadgeClass(status) {
    switch (status) {
        case 'completed':
            return 'badge badge-success';
        case 'failed':
            return 'badge badge-danger';
        case 'running':
        case 'pending':
            return 'badge badge-warning';
        default:
            return 'badge badge-muted';
    }
}

export default function SessionsBrowser() {
    const { user } = useAuth();
    const { notify, confirm } = useUI();
    const [sessions, setSessions] = useState([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [modelCode, setModelCode] = useState('');
    const [status, setStatus] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const totalPages = Math.max(1, Math.ceil(total / LIMIT));

    const fetchSessions = useCallback(async () => {
        if (!user || user.role !== 'admin') return;
        setLoading(true);
        try {
            const params = new URLSearchParams({ page: String(page), limit: String(LIMIT) });
            if (modelCode) params.set('model_code', modelCode);
            if (status) params.set('status', status);
            const data = await api.get(`/admin/sessions?${params.toString()}`, { ttl: 0 });
            setSessions(Array.isArray(data.sessions) ? data.sessions : []);
            setTotal(data.total || 0);
            setError(null);
        } catch (err) {
            setError(err.message || 'Failed to load sessions.');
        } finally {
            setLoading(false);
        }
    }, [user, page, modelCode, status]);

    useEffect(() => {
        fetchSessions();
    }, [fetchSessions]);

    const handleDelete = async (id) => {
        const ok = await confirm({
            title: 'Delete training session?',
            message: 'Delete this training session? This cannot be undone.',
            confirmText: 'Delete',
            danger: true,
        });
        if (!ok) return;
        try {
            await api.delete(`/admin/sessions/${id}`);
            notify('Session deleted.', 'success');
            fetchSessions();
        } catch (err) {
            notify(err.message || 'Failed to delete session.', 'error');
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
            <h2>Training Sessions</h2>
            <div className="admin-toolbar">
                <select
                    value={modelCode}
                    onChange={(e) => { setPage(1); setModelCode(e.target.value); }}
                >
                    <option value="">All models</option>
                    {MODEL_CODES.map((code) => (
                        <option key={code} value={code}>{code}</option>
                    ))}
                </select>
                <select
                    value={status}
                    onChange={(e) => { setPage(1); setStatus(e.target.value); }}
                >
                    {STATUS_OPTIONS.map((s) => (
                        <option key={s || 'all'} value={s}>{s ? s : 'All statuses'}</option>
                    ))}
                </select>
            </div>

            {error && <div className="admin-error-inline">{error}</div>}

            {loading ? (
                <p className="no-data">Loading sessions…</p>
            ) : sessions.length === 0 ? (
                <p className="no-data">No sessions found.</p>
            ) : (
                <div className="admin-table-wrap">
                    <table className="admin-table">
                        <thead>
                            <tr>
                                <th>Session</th>
                                <th>Model</th>
                                <th>User</th>
                                <th>Status</th>
                                <th>Created</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {sessions.map((s) => (
                                <tr key={s._id}>
                                    <td>{s.session_label || '—'}</td>
                                    <td>{s.model_code || '—'}</td>
                                    <td>{s.user_email || s.user_id || '—'}</td>
                                    <td>
                                        <span className={statusBadgeClass(s.status)}>
                                            {s.status || 'unknown'}
                                        </span>
                                    </td>
                                    <td>{s.created_at ? new Date(s.created_at).toLocaleDateString() : '—'}</td>
                                    <td>
                                        <button
                                            className="btn-danger-small"
                                            onClick={() => handleDelete(s._id)}
                                        >
                                            Delete
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            <Pagination
                page={page}
                totalPages={totalPages}
                totalItems={total}
                pageSize={LIMIT}
                onChange={setPage}
                unitLabel="sessions"
            />
        </div>
    );
}
