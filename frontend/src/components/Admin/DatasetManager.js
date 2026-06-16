import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import Pagination from '../shared/Pagination';
import './AdminDashboard.css';
import './Admin.css';

const LIMIT = 20;

const DEFAULT_OPTIONS = [
    { value: '', label: 'All datasets' },
    { value: 'true', label: 'Default only' },
    { value: 'false', label: 'User uploads' },
];

export default function DatasetManager() {
    const { user } = useAuth();
    const [datasets, setDatasets] = useState([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [searchInput, setSearchInput] = useState('');
    const [search, setSearch] = useState('');
    const [isDefault, setIsDefault] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const totalPages = Math.max(1, Math.ceil(total / LIMIT));

    const fetchDatasets = useCallback(async () => {
        if (!user || user.role !== 'admin') return;
        setLoading(true);
        try {
            const params = new URLSearchParams({ page: String(page), limit: String(LIMIT) });
            if (search) params.set('search', search);
            if (isDefault) params.set('is_default', isDefault);
            const data = await api.get(`/admin/datasets?${params.toString()}`, { ttl: 0 });
            setDatasets(Array.isArray(data.datasets) ? data.datasets : []);
            setTotal(data.total || 0);
            setError(null);
        } catch (err) {
            setError(err.message || 'Failed to load datasets.');
        } finally {
            setLoading(false);
        }
    }, [user, page, search, isDefault]);

    useEffect(() => {
        fetchDatasets();
    }, [fetchDatasets]);

    const submitSearch = (e) => {
        e.preventDefault();
        setPage(1);
        setSearch(searchInput.trim());
    };

    const handleToggleDefault = async (id, current) => {
        const next = !current;
        setDatasets((prev) => prev.map((d) => (d._id === id ? { ...d, is_default: next } : d)));
        try {
            await api.patch(`/admin/datasets/${id}/default`, { is_default: next });
        } catch (err) {
            setDatasets((prev) => prev.map((d) => (d._id === id ? { ...d, is_default: current } : d)));
            alert(err.message || 'Failed to update dataset.');
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm('Delete this dataset? This cannot be undone.')) return;
        try {
            await api.delete(`/admin/datasets/${id}`);
            fetchDatasets();
        } catch (err) {
            alert(err.message || 'Failed to delete dataset.');
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
            <h2>Dataset Manager</h2>
            <form className="admin-toolbar" onSubmit={submitSearch}>
                <input
                    type="search"
                    placeholder="Search by filename…"
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
                <select
                    value={isDefault}
                    onChange={(e) => { setPage(1); setIsDefault(e.target.value); }}
                >
                    {DEFAULT_OPTIONS.map((opt) => (
                        <option key={opt.value || 'all'} value={opt.value}>{opt.label}</option>
                    ))}
                </select>
            </form>

            {error && <div className="admin-error-inline">{error}</div>}

            {loading ? (
                <p className="no-data">Loading datasets…</p>
            ) : datasets.length === 0 ? (
                <p className="no-data">No datasets found.</p>
            ) : (
                <div className="admin-table-wrap">
                    <table className="admin-table">
                        <thead>
                            <tr>
                                <th>Filename</th>
                                <th>Owner</th>
                                <th>Type</th>
                                <th>Default</th>
                                <th>Uploaded</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {datasets.map((d) => {
                                const isDef = !!d.is_default;
                                return (
                                    <tr key={d._id}>
                                        <td>{d.filename || '—'}</td>
                                        <td>{d.owner_email || '—'}</td>
                                        <td>{d.file_type || '—'}</td>
                                        <td>
                                            <button
                                                className="admin-btn-secondary"
                                                onClick={() => handleToggleDefault(d._id, isDef)}
                                            >
                                                {isDef
                                                    ? <span className="badge badge-success">Default</span>
                                                    : 'Make default'}
                                            </button>
                                        </td>
                                        <td>{d.uploaded_at ? new Date(d.uploaded_at).toLocaleDateString() : '—'}</td>
                                        <td>
                                            <button
                                                className="btn-danger-small"
                                                onClick={() => handleDelete(d._id)}
                                            >
                                                Delete
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
                unitLabel="datasets"
            />
        </div>
    );
}
