import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import './Dashboard.css';

const Dashboard = () => {
    const { user } = useAuth();
    const [sessions, setSessions] = useState([]);
    const [datasets, setDatasets] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [sessionsRes, datasetsRes] = await Promise.all([
                    api.get('/training-sessions'),
                    api.get('/user-datasets')
                ]);
                setSessions(sessionsRes.sessions || []);
                setDatasets(datasetsRes.datasets || []);
            } catch (err) {
                console.error('Failed to fetch dashboard data:', err);
            }
            setLoading(false);
        };
        fetchData();
    }, []);

    const totalModels = new Set(sessions.map(s => s.model_code)).size;
    const completedSessions = sessions.filter(s => s.status === 'completed');
    const avgAccuracy = completedSessions.length > 0
        ? (completedSessions.reduce((sum, s) => sum + (s.results?.accuracy || 0), 0) / completedSessions.length * 100).toFixed(1)
        : 'N/A';

    if (loading) {
        return (
            <div className="loading-screen">
                <div className="spinner"></div>
                <p>Loading dashboard...</p>
            </div>
        );
    }

    return (
        <div className="dashboard">
            <div className="dashboard-header">
                <h1>Dashboard</h1>
                <p>Welcome back, <strong>{user?.first_name || 'User'}</strong></p>
            </div>

            {/* Stats */}
            <div className="stats-grid">
                <div className="stat-card">
                    <span className="stat-icon">🧠</span>
                    <div>
                        <span className="stat-number">{sessions.length}</span>
                        <span className="stat-text">Training Sessions</span>
                    </div>
                </div>
                <div className="stat-card">
                    <span className="stat-icon">📂</span>
                    <div>
                        <span className="stat-number">{datasets.length}</span>
                        <span className="stat-text">Datasets</span>
                    </div>
                </div>
                <div className="stat-card">
                    <span className="stat-icon">🤖</span>
                    <div>
                        <span className="stat-number">{totalModels}</span>
                        <span className="stat-text">Models Used</span>
                    </div>
                </div>
                <div className="stat-card">
                    <span className="stat-icon">🎯</span>
                    <div>
                        <span className="stat-number">{avgAccuracy}%</span>
                        <span className="stat-text">Avg Accuracy</span>
                    </div>
                </div>
            </div>

            {/* Recent Sessions */}
            <div className="dashboard-section">
                <h2>Recent Training Sessions</h2>
                {sessions.length === 0 ? (
                    <div className="empty-state">
                        <p>No training sessions yet. Head to the <a href="/lab">Lab</a> to train your first model!</p>
                    </div>
                ) : (
                    <div className="sessions-table">
                        <table>
                            <thead>
                                <tr>
                                    <th>Model</th>
                                    <th>Version</th>
                                    <th>Status</th>
                                    <th>Date</th>
                                    <th>Key Metric</th>
                                </tr>
                            </thead>
                            <tbody>
                                {sessions.slice(0, 10).map((s) => (
                                    <tr key={s._id}>
                                        <td className="model-cell">
                                            <span className="model-badge">{s.model_code}</span>
                                        </td>
                                        <td>v{s.version}</td>
                                        <td>
                                            <span className={`status-badge status-${s.status}`}>
                                                {s.status}
                                            </span>
                                        </td>
                                        <td>{new Date(s.created_at).toLocaleDateString()}</td>
                                        <td>
                                            {s.results?.accuracy
                                                ? `${(s.results.accuracy * 100).toFixed(1)}%`
                                                : s.results?.R2
                                                ? `R²: ${s.results.R2.toFixed(3)}`
                                                : '—'
                                            }
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Datasets */}
            <div className="dashboard-section">
                <h2>Your Datasets</h2>
                {datasets.length === 0 ? (
                    <div className="empty-state">
                        <p>No datasets uploaded yet.</p>
                    </div>
                ) : (
                    <div className="datasets-grid">
                        {datasets.map((d) => (
                            <div className="dataset-card" key={d._id}>
                                <span className="dataset-icon">📄</span>
                                <div className="dataset-info">
                                    <span className="dataset-name">{d.filename}</span>
                                    <span className="dataset-date">{new Date(d.uploaded_at).toLocaleDateString()}</span>
                                </div>
                                <span className="dataset-type">{d.file_type}</span>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default Dashboard;
