import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import Pagination from '../shared/Pagination';
import './AdminDashboard.css';
import './Admin.css';

const LIMIT = 20;

export default function UserManagement() {
    const { user } = useAuth();
    const [users, setUsers] = useState([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [searchInput, setSearchInput] = useState('');
    const [search, setSearch] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const totalPages = Math.max(1, Math.ceil(total / LIMIT));

    const fetchUsers = useCallback(async () => {
        if (!user || user.role !== 'admin') return;
        setLoading(true);
        try {
            const params = new URLSearchParams({ page: String(page), limit: String(LIMIT) });
            if (search) params.set('search', search);
            const data = await api.get(`/admin/users?${params.toString()}`, { ttl: 0 });
            setUsers(Array.isArray(data.users) ? data.users : []);
            setTotal(data.total || 0);
            setError(null);
        } catch (err) {
            setError(err.message || 'Failed to load users.');
        } finally {
            setLoading(false);
        }
    }, [user, page, search]);

    useEffect(() => {
        fetchUsers();
    }, [fetchUsers]);

    const submitSearch = (e) => {
        e.preventDefault();
        setPage(1);
        setSearch(searchInput.trim());
    };

    const handleRoleChange = async (id, newRole, prevRole) => {
        // Optimistic update.
        setUsers((prev) => prev.map((u) => (u._id === id ? { ...u, role: newRole } : u)));
        try {
            await api.patch(`/admin/users/${id}/role`, { role: newRole });
        } catch (err) {
            // Revert on failure (e.g. backend blocks removing your own admin role).
            setUsers((prev) => prev.map((u) => (u._id === id ? { ...u, role: prevRole } : u)));
            alert(err.message || 'Failed to update role.');
        }
    };

    const handleStatusToggle = async (id, current) => {
        const next = !current;
        setUsers((prev) => prev.map((u) => (u._id === id ? { ...u, active: next } : u)));
        try {
            await api.patch(`/admin/users/${id}/status`, { active: next });
        } catch (err) {
            setUsers((prev) => prev.map((u) => (u._id === id ? { ...u, active: current } : u)));
            alert(err.message || 'Failed to update status.');
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
            <h2>User Management</h2>
            <form className="admin-toolbar" onSubmit={submitSearch}>
                <input
                    type="search"
                    placeholder="Search by email or name…"
                    value={searchInput}
                    onChange={(e) => setSearchInput(e.target.value)}
                />
                <button type="submit" className="admin-btn">Search</button>
                {search && (
                    <button
                        type="button"
                        className="admin-btn-secondary"
                        onClick={() => { setSearchInput(''); setSearch(''); setPage(1); }}
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
                                <th>Sessions</th>
                                <th>Datasets</th>
                                <th>Joined</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {users.map((u) => {
                                const isActive = u.active !== false;
                                const name = [u.first_name, u.last_name].filter(Boolean).join(' ') || '—';
                                return (
                                    <tr key={u._id}>
                                        <td>{u.email || '—'}</td>
                                        <td>{name}</td>
                                        <td>
                                            <select
                                                className="role-select"
                                                value={u.role || 'user'}
                                                onChange={(e) => handleRoleChange(u._id, e.target.value, u.role || 'user')}
                                            >
                                                <option value="user">user</option>
                                                <option value="admin">admin</option>
                                            </select>
                                        </td>
                                        <td>{u.plan || '—'}</td>
                                        <td>{u.session_count != null ? u.session_count : 0}</td>
                                        <td>{u.dataset_count != null ? u.dataset_count : 0}</td>
                                        <td>{u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}</td>
                                        <td>
                                            <button
                                                className="admin-btn-secondary"
                                                onClick={() => handleStatusToggle(u._id, isActive)}
                                            >
                                                {isActive ? 'Deactivate' : 'Activate'}
                                            </button>
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
        </div>
    );
}
