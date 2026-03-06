import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
import DownloadResultsZip from '../DownloadResultsZip/DownloadResultsZip';
import './Dashboard.css';

const Dashboard = () => {
    const { user } = useAuth();
    const [sessions, setSessions] = useState([]);
    const [datasets, setDatasets] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showFeedback, setShowFeedback] = useState(false);
    const [feedbackMsg, setFeedbackMsg] = useState('');
    const [feedbackType, setFeedbackType] = useState('general');
    const [toast, setToast] = useState(null); // { type: 'success' | 'error', message: string }
    const [confirmDelete, setConfirmDelete] = useState(null); // { sessionId, modelCode } or null

    useEffect(() => {
        const fetchData = async () => {
            try {
                const sessionsRes = await api.get('/training-sessions');
                const datasetsRes = await api.get('/user-datasets');

                console.log('Sessions raw response:', sessionsRes);

                // Be defensive about response shape:
                // - { sessions: [...] }
                // - { data: { sessions: [...] } }
                // - direct array [...]
                let sessionsData = [];
                if (Array.isArray(sessionsRes)) {
                    sessionsData = sessionsRes;
                } else if (Array.isArray(sessionsRes.sessions)) {
                    sessionsData = sessionsRes.sessions;
                } else if (sessionsRes.data && Array.isArray(sessionsRes.data.sessions)) {
                    sessionsData = sessionsRes.data.sessions;
                }

                let datasetsData = [];
                if (Array.isArray(datasetsRes)) {
                    datasetsData = datasetsRes;
                } else if (Array.isArray(datasetsRes.datasets)) {
                    datasetsData = datasetsRes.datasets;
                } else if (datasetsRes.data && Array.isArray(datasetsRes.data.datasets)) {
                    datasetsData = datasetsRes.data.datasets;
                }

                console.log('Parsed sessions count:', sessionsData.length);
                console.log('Parsed datasets count:', datasetsData.length);

                setSessions(sessionsData);
                setDatasets(datasetsData);
            } catch (err) {
                console.error('Failed to fetch dashboard data:', err);
                setSessions([]);
                setDatasets([]);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const handleDeleteSession = async (sessionId, modelCode) => {
        try {
            await api.delete(`/training-sessions/${sessionId}`);
            setSessions(prev => prev.filter(s => s._id !== sessionId));
            setToast({ type: 'success', message: `${modelCode} session deleted.` });
        } catch (err) {
            console.error('Failed to delete session:', err);
            setToast({ type: 'error', message: 'Failed to delete session. Please try again.' });
        }
    };

    const handleFeedbackSubmit = async (e) => {
        e.preventDefault();
        const trimmedMsg = feedbackMsg.trim();
        
        if (!trimmedMsg) {
            setToast({ type: 'error', message: 'Please provide feedback message.' });
            return;
        }

        try {
                const res = await api.post('/feedback', { 
                    message: trimmedMsg, 
                    type: feedbackType,
                    source: 'dashboard',
                    path: window.location?.pathname || '/dashboard',
                    timestamp: new Date().toISOString()
                });
            
            if (res.message || res.success || res.feedback_id) {
                setToast({ type: 'success', message: 'Thank you for your feedback! We appreciate your input.' });
                setShowFeedback(false);
                setFeedbackMsg('');
                setFeedbackType('general');
            }
        } catch (err) {
            console.error('Failed to submit feedback:', err);
            setToast({ type: 'error', message: 'Failed to submit feedback. Please try again.' });
        }
    };

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
            {/* Toast notification */}
            {toast && (
                <div
                    className={`dashboard-toast dashboard-toast-${toast.type}`}
                    onAnimationEnd={() => setToast(null)}
                >
                    {toast.message}
                </div>
            )}

            <div className="dashboard-header">
                <div>
                    <h1>Dashboard</h1>
                    <p>Welcome back, <strong>{user?.first_name || 'User'}</strong></p>
                </div>
                <button 
                    className="btn-feedback" 
                    onClick={() => setShowFeedback(true)}
                >
                    💬 Give Feedback
                </button>
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
                                    <th>Trained Model</th>
                                    <th>Training Results</th>
                                    <th style={{ width: '50px' }}>Action</th>
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
                                        <td>
                                            {s.status === 'completed' && (
                                                <DownloadTrainedModel 
                                                    selectedModel={s.model_code} 
                                                    extension={['cnn', 'ann', 'lstm', 'resnet', 'stylegan'].includes(s.model_code) ? '.h5' : s.model_code === 'object_detection' ? '.pt' : '.pkl'} 
                                                    sessionId={s._id} 
                                                    label="Download"
                                                />
                                            )}
                                        </td>
                                        <td>
                                            {s.status === 'completed' && s.results_zip_drive_id && (
                                                <DownloadResultsZip sessionId={s._id} label="Download" />
                                            )}
                                        </td>
                                        <td className="action-cell">
                                            <button 
                                                className="btn-delete-session"
                                                onClick={() => setConfirmDelete({ sessionId: s._id, modelCode: s.model_code })}
                                                title="Delete this session"
                                            >
                                                🗑️
                                            </button>
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

            {/* Feedback Modal */}
            {showFeedback && (
                <div className="modal-overlay" onClick={() => setShowFeedback(false)}>
                    <div className="feedback-modal" onClick={e => e.stopPropagation()}>
                        <h2>Give Feedback</h2>
                        <form onSubmit={handleFeedbackSubmit}>
                            <div className="form-group">
                                <label>Feedback Type</label>
                                <select 
                                    value={feedbackType} 
                                    onChange={e => setFeedbackType(e.target.value)}
                                >
                                    <option value="general">General Suggestion</option>
                                    <option value="bug">Report a Bug</option>
                                    <option value="model">Model Request</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label>Message</label>
                                <textarea 
                                    required
                                    rows="4"
                                    value={feedbackMsg}
                                    onChange={e => setFeedbackMsg(e.target.value)}
                                    placeholder="Tell us what you think..."
                                ></textarea>
                            </div>
                            <div className="modal-actions">
                                <button type="button" className="btn-secondary" onClick={() => setShowFeedback(false)}>Cancel</button>
                                <button type="submit" className="btn-primary">Submit Feedback</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Delete confirmation modal */}
            {confirmDelete && (
                <div className="modal-overlay" onClick={() => setConfirmDelete(null)}>
                    <div className="feedback-modal" onClick={e => e.stopPropagation()}>
                        <h2>Delete Training Session</h2>
                        <p style={{ marginTop: '0.5rem', marginBottom: '1.5rem', color: 'var(--text-secondary)' }}>
                            This will remove the <strong>{confirmDelete.modelCode}</strong> session,
                            its trained model and associated files. This action cannot be undone.
                        </p>
                        <div className="modal-actions">
                            <button
                                type="button"
                                className="btn-secondary"
                                onClick={() => setConfirmDelete(null)}
                            >
                                Cancel
                            </button>
                            <button
                                type="button"
                                className="btn-primary"
                                onClick={async () => {
                                    const { sessionId, modelCode } = confirmDelete;
                                    setConfirmDelete(null);
                                    await handleDeleteSession(sessionId, modelCode);
                                }}
                                style={{ background: 'linear-gradient(135deg, #ff5f6d 0%, #ffc371 100%)' }}
                            >
                                Yes, delete
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Dashboard;
