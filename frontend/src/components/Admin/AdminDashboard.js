import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useUI } from '../../context/UIDialog';
import api from '../../services/api';
import './AdminDashboard.css';

const STAT_CARDS = [
    ['total_users', 'Total users'],
    ['active_users_7d', 'Active (7 days)'],
    ['new_users_today', 'New today'],
    ['deactivated_users', 'Deactivated'],
    ['total_sessions', 'Training sessions'],
    ['running_sessions', 'Running now'],
    ['total_datasets', 'Datasets'],
    ['open_feedback', 'Open feedback'],
];

const AdminDashboard = () => {
    const { user } = useAuth();
    const { notify, confirm } = useUI();
    const [stats, setStats] = useState(null);
    const [datasets, setDatasets] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const [statsData, dsData] = await Promise.all([
                api.get('/admin/stats', { force: true }),
                api.get('/admin/datasets/default', { force: true }),
            ]);
            setStats(statsData);
            setDatasets(dsData.datasets || []);
            setError(null);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { load(); }, [load]);

    const handleDeleteDataset = async (datasetId) => {
        const ok = await confirm({
            title: 'Remove default dataset?',
            message: 'It will no longer appear in the public dataset library.',
            confirmText: 'Remove',
            danger: true,
        });
        if (!ok) return;
        try {
            await api.delete(`/admin/datasets/default/${datasetId}`);
            setDatasets((list) => list.filter((d) => d._id !== datasetId));
            notify('Default dataset removed.', 'success');
        } catch (err) {
            notify(err.message || 'Failed to delete dataset', 'error');
        }
    };

    if (loading) return <div className="admin-loading">Loading admin dashboard…</div>;
    if (error) {
        return (
            <div className="admin-error">
                <p>Error: {error}</p>
                <button type="button" className="admin-btn" onClick={load}>Retry</button>
            </div>
        );
    }

    return (
        <div className="admin-dashboard">
            <header className="admin-header">
                <h1>Platform Administration</h1>
                <p>Welcome back, {user?.first_name}</p>
            </header>

            <div className="admin-stats-grid">
                {STAT_CARDS.map(([key, label]) => (
                    <div className="stat-card" key={key}>
                        <h3>{label}</h3>
                        <div className="stat-value">{(stats?.[key] ?? 0).toLocaleString()}</div>
                    </div>
                ))}
            </div>

            <div className="admin-content">
                <div className="admin-section models-chart">
                    <h2>Training by model</h2>
                    <ul className="model-stats-list">
                        {stats?.sessions_by_model?.map((m) => (
                            <li key={m._id || 'unknown'}>
                                <span>{m._id || 'unknown'}</span>
                                <strong>{m.count}</strong>
                            </li>
                        ))}
                    </ul>
                </div>

                <div className="admin-section dataset-manager">
                    <h2>Default datasets library</h2>
                    <p className="section-desc">The curated datasets available to every user.</p>
                    {datasets.length === 0 ? (
                        <p className="no-data">No default datasets in the library yet.</p>
                    ) : (
                        <div className="admin-table-wrap">
                            <table className="admin-table">
                                <thead>
                                    <tr>
                                        <th>Filename</th>
                                        <th>Type</th>
                                        <th>Uploaded</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {datasets.map((d) => (
                                        <tr key={d._id}>
                                            <td>{d.filename}</td>
                                            <td>{d.file_type}</td>
                                            <td>{d.uploaded_at ? new Date(d.uploaded_at).toLocaleDateString() : '—'}</td>
                                            <td>
                                                <button type="button" className="btn-danger-small" onClick={() => handleDeleteDataset(d._id)}>
                                                    Remove
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default AdminDashboard;
