import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { API_URL } from '../../constants';
import './AdminDashboard.css';

const AdminDashboard = () => {
    const { user, token } = useAuth();
    const [stats, setStats] = useState(null);
    const [datasets, setDatasets] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchAdminData = async () => {
            try {
                setLoading(true);
                const [statsRes, dsRes] = await Promise.all([
                    fetch(`${API_URL}/admin/stats`, {
                        headers: { 'Authorization': `Bearer ${token}` }
                    }),
                    fetch(`${API_URL}/admin/datasets/default`, {
                        headers: { 'Authorization': `Bearer ${token}` }
                    })
                ]);

                if (!statsRes.ok || !dsRes.ok) throw new Error("Failed to fetch admin data.");

                const statsData = await statsRes.json();
                const dsData = await dsRes.json();

                setStats(statsData);
                setDatasets(dsData.datasets);
                setError(null);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        if (user && user.role === 'admin') {
            fetchAdminData();
        }
    }, [user, token]);

    const handleDeleteDataset = async (datasetId) => {
        if (window.confirm("Are you sure you want to remove this default dataset?")) {
            try {
                const res = await fetch(`${API_URL}/admin/datasets/default/${datasetId}`, {
                    method: 'DELETE',
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (res.ok) {
                    setDatasets(datasets.filter(d => d._id !== datasetId));
                } else {
                    alert('Failed to delete dataset');
                }
            } catch (err) {
                console.error(err);
            }
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

    if (loading) return <div className="admin-loading">Loading Admin Dashboard...</div>;
    if (error) return <div className="admin-error">Error: {error}</div>;

    return (
        <div className="admin-dashboard">
            <header className="admin-header">
                <h1>Platform Administration</h1>
                <p>Welcome back, Administrator {user.first_name}</p>
            </header>

            <div className="admin-stats-grid">
                <div className="stat-card">
                    <h3>Total Users</h3>
                    <div className="stat-value">{stats?.total_users || 0}</div>
                </div>
                <div className="stat-card">
                    <h3>Training Sessions</h3>
                    <div className="stat-value">{stats?.total_sessions || 0}</div>
                </div>
                <div className="stat-card">
                    <h3>Datasets Uploaded</h3>
                    <div className="stat-value">{stats?.total_datasets || 0}</div>
                </div>
            </div>

            <div className="admin-content">
                <div className="admin-section models-chart">
                    <h2>Training by Model</h2>
                    <ul className="model-stats-list">
                        {stats?.sessions_by_model?.map((m, idx) => (
                            <li key={idx}>
                                <span>{m._id}</span>
                                <strong>{m.count}</strong>
                            </li>
                        ))}
                    </ul>
                </div>

                <div className="admin-section dataset-manager">
                    <h2>Default Datasets Library</h2>
                    <p className="section-desc">Manage the curated list of default datasets available to all users.</p>
                    
                    {datasets.length === 0 ? (
                        <p className="no-data">No default datasets currently marked in the library.</p>
                    ) : (
                        <table className="admin-table">
                            <thead>
                                <tr>
                                    <th>Filename</th>
                                    <th>Type</th>
                                    <th>Upload Date</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {datasets.map((d) => (
                                    <tr key={d._id}>
                                        <td>{d.filename}</td>
                                        <td>{d.file_type}</td>
                                        <td>{new Date(d.uploaded_at).toLocaleDateString()}</td>
                                        <td>
                                            <button 
                                                className="btn-danger-small"
                                                onClick={() => handleDeleteDataset(d._id)}
                                            >
                                                Remove 🗑️
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>
        </div>
    );
};

export default AdminDashboard;
