import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useUI } from '../../context/UIDialog';
import api from '../../services/api';
import Pagination from '../shared/Pagination';
import './AdminDashboard.css';
import './Admin.css';

const LIMIT = 20;
const PLANS = ['free', 'pro', 'team'];

const fmtDate = (v) => (v ? new Date(v).toLocaleDateString() : '—');
const fmtDateTime = (v) => (v ? new Date(v).toLocaleString() : '—');

function UserDetail({ userId, onClose }) {
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        let active = true;
        api.get(`/admin/users/${userId}`, { ttl: 0 })
            .then((d) => active && setData(d))
            .catch((e) => active && setError(e.message));
        return () => { active = false; };
    }, [userId]);

    useEffect(() => {
        const onKey = (e) => e.key === 'Escape' && onClose();
        window.addEventListener('keydown', onKey);
        return () => window.removeEventListener('keydown', onKey);
    }, [onClose]);

    const u = data?.user;
    return (
        <div className="admin-drawer-overlay" onClick={onClose}>
            <aside className="admin-drawer" role="dialog" aria-modal="true" aria-label="User details"
                onClick={(e) => e.stopPropagation()}>
                <header className="admin-drawer-head">
                    <h3>{u ? ([u.first_name, u.last_name].filter(Boolean).join(' ') || u.email) : 'User details'}</h3>
                    <button type="button" className="admin-btn-secondary" onClick={onClose} aria-label="Close">✕</button>
                </header>
                {error && <div className="admin-error-inline">{error}</div>}
                {!data && !error && <p className="no-data">Loading…</p>}
                {u && (
                    <>
                        <dl className="admin-dl">
                            <dt>Email</dt><dd>{u.email}{u.email_verified ? ' ✓' : ' (unverified)'}</dd>
                            <dt>Role</dt><dd>{u.role || 'user'}</dd>
                            <dt>Status</dt><dd>{u.active === false ? 'Deactivated' : 'Active'}</dd>
                            <dt>Plan</dt><dd>{u.subscription?.plan || 'free'}{u.subscription?.provider ? ` (${u.subscription.provider})` : ''}</dd>
                            <dt>Sign-in</dt><dd>{u.oauth_provider ? `OAuth (${u.oauth_provider})` : 'Password'}</dd>
                            <dt>Joined</dt><dd>{fmtDateTime(u.created_at)}</dd>
                            <dt>Last login</dt><dd>{fmtDateTime(u.last_login)}</dd>
                        </dl>
                        <h4>Storage</h4>
                        <div className="admin-mini-stats">
                            <span><strong>{data.storage.datasets}</strong> datasets</span>
                            <span><strong>{data.storage.training_sessions}</strong> runs</span>
                            <span><strong>{data.storage.pipelines}</strong> pipelines</span>
                        </div>
                        <h4>Usage this month ({data.usage.period})</h4>
                        <div className="admin-mini-stats">
                            {['classical', 'deep', 'finetune', 'datastudio'].map((k) => (
                                <span key={k}><strong>{data.usage[k] || 0}</strong> {k}</span>
                            ))}
                        </div>
                        <h4>Recent runs</h4>
                        {data.recent_sessions.length === 0 ? <p className="no-data">No runs yet.</p> : (
                            <ul className="admin-recent">
                                {data.recent_sessions.map((s) => (
                                    <li key={s._id}>
                                        <span>{s.model_code} v{s.version}</span>
                                        <span className={`badge ${s.status === 'completed' ? 'badge-success' : s.status === 'failed' ? 'badge-danger' : 'badge-muted'}`}>{s.status}</span>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </>
                )}
            </aside>
        </div>
    );
}

export default function UserManagement() {
    const { user } = useAuth();
    const { notify, confirm } = useUI();
    const [users, setUsers] = useState([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [searchInput, setSearchInput] = useState('');
    const [filters, setFilters] = useState({ search: '', role: '', status: '', plan: '' });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [detailId, setDetailId] = useState(null);

    const totalPages = Math.max(1, Math.ceil(total / LIMIT));

    const fetchUsers = useCallback(async () => {
        setLoading(true);
        try {
            const params = new URLSearchParams({ page: String(page), limit: String(LIMIT) });
            Object.entries(filters).forEach(([k, v]) => { if (v) params.set(k, v); });
            const data = await api.get(`/admin/users?${params.toString()}`, { ttl: 0 });
            setUsers(Array.isArray(data.users) ? data.users : []);
            setTotal(data.total || 0);
            setError(null);
        } catch (err) {
            setError(err.message || 'Failed to load users.');
        } finally {
            setLoading(false);
        }
    }, [page, filters]);

    useEffect(() => { fetchUsers(); }, [fetchUsers]);

    const setFilter = (key, value) => {
        setPage(1);
        setFilters((f) => ({ ...f, [key]: value }));
    };

    const submitSearch = (e) => {
        e.preventDefault();
        setFilter('search', searchInput.trim());
    };

    const patchUser = async (id, patch, request, failMsg) => {
        const prev = users.find((u) => u._id === id);
        setUsers((list) => list.map((u) => (u._id === id ? { ...u, ...patch } : u)));
        try {
            await request();
        } catch (err) {
            setUsers((list) => list.map((u) => (u._id === id ? prev : u)));
            notify(err.message || failMsg, 'error');
        }
    };

    const handleRoleChange = (id, role) =>
        patchUser(id, { role }, () => api.patch(`/admin/users/${id}/role`, { role }), 'Failed to update role.');

    const handlePlanChange = (id, plan) =>
        patchUser(id, { plan }, () => api.patch(`/admin/users/${id}/plan`, { plan }), 'Failed to update plan.');

    const handleStatusToggle = async (u) => {
        const next = u.active === false;
        if (!next) {
            const ok = await confirm({
                title: 'Deactivate user?',
                message: `${u.email} will be signed out everywhere and blocked from signing in until reactivated.`,
                confirmText: 'Deactivate',
                danger: true,
            });
            if (!ok) return;
        }
        patchUser(u._id, { active: next }, () => api.patch(`/admin/users/${u._id}/status`, { active: next }), 'Failed to update status.');
    };

    const handleRevoke = async (u) => {
        const ok = await confirm({
            title: 'Sign this user out everywhere?',
            message: `All active sessions for ${u.email} will be revoked.`,
            confirmText: 'Revoke sessions',
        });
        if (!ok) return;
        try {
            await api.post(`/admin/users/${u._id}/revoke-sessions`, {});
            notify('Sessions revoked.', 'success');
        } catch (err) {
            notify(err.message || 'Failed to revoke sessions.', 'error');
        }
    };

    const handleDelete = async (u) => {
        const ok = await confirm({
            title: 'Delete user permanently?',
            message: `${u.email} and all of their datasets, trained models and history will be permanently deleted. This cannot be undone.`,
            confirmText: 'Delete user',
            danger: true,
        });
        if (!ok) return;
        try {
            await api.delete(`/admin/users/${u._id}`);
            notify('User deleted.', 'success');
            fetchUsers();
        } catch (err) {
            notify(err.message || 'Failed to delete user.', 'error');
        }
    };

    return (
        <div className="admin-section">
            <h2>User management</h2>
            <form className="admin-toolbar" onSubmit={submitSearch}>
                <input
                    type="search"
                    placeholder="Search by email or name…"
                    value={searchInput}
                    onChange={(e) => setSearchInput(e.target.value)}
                    aria-label="Search users"
                />
                <select value={filters.role} onChange={(e) => setFilter('role', e.target.value)} aria-label="Filter by role">
                    <option value="">All roles</option>
                    <option value="user">Users</option>
                    <option value="admin">Admins</option>
                </select>
                <select value={filters.status} onChange={(e) => setFilter('status', e.target.value)} aria-label="Filter by status">
                    <option value="">Any status</option>
                    <option value="active">Active</option>
                    <option value="inactive">Deactivated</option>
                </select>
                <select value={filters.plan} onChange={(e) => setFilter('plan', e.target.value)} aria-label="Filter by plan">
                    <option value="">Any plan</option>
                    {PLANS.map((p) => <option key={p} value={p}>{p}</option>)}
                </select>
                <button type="submit" className="admin-btn">Search</button>
                {(filters.search || filters.role || filters.status || filters.plan) && (
                    <button
                        type="button"
                        className="admin-btn-secondary"
                        onClick={() => { setSearchInput(''); setPage(1); setFilters({ search: '', role: '', status: '', plan: '' }); }}
                    >
                        Clear
                    </button>
                )}
            </form>

            {error && <div className="admin-error-inline">{error}</div>}

            {loading ? (
                <p className="no-data">Loading users…</p>
            ) : users.length === 0 ? (
                <p className="no-data">No users found.</p>
            ) : (
                <div className="admin-table-wrap">
                    <table className="admin-table">
                        <thead>
                            <tr>
                                <th>Email</th>
                                <th>Name</th>
                                <th>Role</th>
                                <th>Plan</th>
                                <th>Runs</th>
                                <th>Datasets</th>
                                <th>Joined</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {users.map((u) => {
                                const isActive = u.active !== false;
                                const isSelf = u._id === user?._id;
                                const name = [u.first_name, u.last_name].filter(Boolean).join(' ') || '—';
                                return (
                                    <tr key={u._id} className={isActive ? '' : 'row-muted'}>
                                        <td>
                                            <button type="button" className="admin-link" onClick={() => setDetailId(u._id)}>
                                                {u.email || '—'}
                                            </button>
                                            {!isActive && <span className="badge badge-danger">deactivated</span>}
                                        </td>
                                        <td>{name}</td>
                                        <td>
                                            <select className="role-select" value={u.role || 'user'} disabled={isSelf}
                                                onChange={(e) => handleRoleChange(u._id, e.target.value)} aria-label={`Role for ${u.email}`}>
                                                <option value="user">user</option>
                                                <option value="admin">admin</option>
                                            </select>
                                        </td>
                                        <td>
                                            <select className="role-select" value={u.plan || 'free'}
                                                onChange={(e) => handlePlanChange(u._id, e.target.value)} aria-label={`Plan for ${u.email}`}>
                                                {PLANS.map((p) => <option key={p} value={p}>{p}</option>)}
                                            </select>
                                        </td>
                                        <td>{u.session_count ?? 0}</td>
                                        <td>{u.dataset_count ?? 0}</td>
                                        <td>{fmtDate(u.created_at)}</td>
                                        <td>
                                            <div className="admin-row-actions">
                                                <button type="button" className="admin-btn-secondary" disabled={isSelf}
                                                    onClick={() => handleStatusToggle(u)}>
                                                    {isActive ? 'Deactivate' : 'Activate'}
                                                </button>
                                                <button type="button" className="admin-btn-secondary" onClick={() => handleRevoke(u)}>
                                                    Sign out
                                                </button>
                                                <button type="button" className="btn-danger-small" disabled={isSelf} onClick={() => handleDelete(u)}>
                                                    Delete
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                );
                            })}
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
                unitLabel="users"
            />

            {detailId && <UserDetail userId={detailId} onClose={() => setDetailId(null)} />}
        </div>
    );
}
