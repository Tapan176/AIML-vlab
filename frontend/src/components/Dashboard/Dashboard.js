import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlayCircle, faFileAlt, faRobot, faCircleCheck, faRedo } from '@fortawesome/free-solid-svg-icons';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
import DownloadResultsZip from '../DownloadResultsZip/DownloadResultsZip';
import { useModelRegistry, getModelExtension } from '../../hooks/useModelRegistry';
import { truncateName } from '../../utils/truncateName';
import usePagination from '../../hooks/usePagination';
import Pagination from '../shared/Pagination';
import RunComparison from './RunComparison';
import PredictModal from './PredictModal';
import Leaderboard from './Leaderboard';
import OnboardingModal, { ONBOARDING_DISMISSED_KEY } from '../Onboarding/OnboardingModal';
import { SkeletonCard, SkeletonRows } from '../shared/Skeleton';
import './Dashboard.css';

const Dashboard = () => {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [sessions, setSessions] = useState([]);
    const [datasets, setDatasets] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showFeedback, setShowFeedback] = useState(false);
    const [feedbackMsg, setFeedbackMsg] = useState('');
    const [feedbackType, setFeedbackType] = useState('general');
    const [toast, setToast] = useState(null); // { type: 'success' | 'error', message: string }
    const [confirmDelete, setConfirmDelete] = useState(null); // { sessionId, modelCode } or null
    // Run-comparison (D2): which sessions are ticked, and whether the modal is open.
    const [compareIds, setCompareIds] = useState([]);
    const [showCompare, setShowCompare] = useState(false);
    // Predict-on-new-data (D3): the session whose model we're predicting with.
    const [predictSession, setPredictSession] = useState(null);
    // First-run onboarding (D4): shown once when a brand-new user has no runs.
    const [showOnboarding, setShowOnboarding] = useState(false);
    const registry = useModelRegistry();

    const toggleCompare = (id) => {
        setCompareIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
    };

    // A classical model (predict-on-new-data supported): not streaming + not fine-tuning.
    const isClassical = (modelCode) => {
        const m = registry?.models?.[modelCode];
        if (!m) return false;
        return !m.streaming && m.category !== 'Fine-Tuning';
    };

    useEffect(() => {
        const fetchData = async () => {
            try {
                // force: skip the GET cache so a session created by an SSE
                // training run (which doesn't go through api.*) shows up here.
                const sessionsRes = await api.get('/training-sessions', { force: true });
                const datasetsRes = await api.get('/user-datasets', { force: true });

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

                setSessions(sessionsData);
                setDatasets(datasetsData);

                // First-run onboarding: only for a genuinely new user (no
                // sessions yet) who hasn't dismissed it before.
                try {
                    const dismissed = localStorage.getItem(ONBOARDING_DISMISSED_KEY);
                    if (!dismissed && sessionsData.length === 0) setShowOnboarding(true);
                } catch (e) {}
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

    const handleReplaySession = (session) => {
        // The session identity goes in the URL (/lab/:modelCode?session=<id>) so
        // it survives a refresh and a navigate-away-then-back: the model page
        // re-attaches to live progress (or restores completed results) purely
        // from the URL. The one-shot sessionStorage payload below only seeds the
        // form values that aren't in the URL (hyperparams + dataset_config).
        sessionStorage.setItem('replay_session', JSON.stringify({
            session_id: session._id,
            status: session.status,
            hyperparams: session.hyperparams,
            model_code: session.model_code,
            dataset_info: session.dataset_info,
            dataset_config: session.dataset_config || {},
        }));
        // Also store the dataset selection in localStorage using the model's cache
        // key, including the ids so the dataset dropdown can re-select it.
        if (session.dataset_info?.filename) {
            localStorage.setItem(`${session.model_code}_dataset`, JSON.stringify({
                filename: session.dataset_info.filename,
                file_type: session.dataset_info.file_type || 'csv',
                dataset_id: session.dataset_info.dataset_id || null,
                drive_id: session.dataset_info.drive_id || null,
            }));
        }
        // Navigate straight to the model page with the session id in the URL.
        navigate(`/lab/${session.model_code}?session=${session._id}`);
        setToast({ type: 'success', message: `Loading ${session.model_code} with previous configuration...` });
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

    // Paginate both lists client-side (the endpoints return everything,
    // sorted newest-first) so each section stays compact on the dashboard.
    const sessionsPage = usePagination(sessions, 10);
    const datasetsPage = usePagination(datasets, 8);

    if (loading) {
        return (
            <div className="dashboard">
                <div className="dashboard-header">
                    <div>
                        <h1>Dashboard</h1>
                        <p>Loading your workspace…</p>
                    </div>
                </div>
                <div className="dashboard-section">
                    <h2>Recent Training Sessions</h2>
                    <SkeletonRows rows={5} cols={5} />
                </div>
                <div className="dashboard-section">
                    <h2>Your Datasets</h2>
                    <div className="datasets-grid">
                        {Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} lines={2} />)}
                    </div>
                </div>
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
                    <span className="stat-icon">
                        <FontAwesomeIcon icon={faPlayCircle} />
                    </span>
                    <div>
                        <span className="stat-number">{sessions.length}</span>
                        <span className="stat-text">Training Sessions</span>
                    </div>
                </div>
                <div className="stat-card">
                    <span className="stat-icon">
                        <FontAwesomeIcon icon={faFileAlt} />
                    </span>
                    <div>
                        <span className="stat-number">{datasets.length}</span>
                        <span className="stat-text">Datasets</span>
                    </div>
                </div>
                <div className="stat-card">
                    <span className="stat-icon">
                        <FontAwesomeIcon icon={faRobot} />
                    </span>
                    <div>
                        <span className="stat-number">{totalModels}</span>
                        <span className="stat-text">Models Used</span>
                    </div>
                </div>
                <div className="stat-card">
                    <span className="stat-icon">
                        <FontAwesomeIcon icon={faCircleCheck} />
                    </span>
                    <div>
                        <span className="stat-number">{completedSessions.length}</span>
                        <span className="stat-text">Completed Runs</span>
                    </div>
                </div>
            </div>

            {/* Recent Sessions */}
            <div className="dashboard-section">
                <div className="section-header-row" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap' }}>
                    <h2 style={{ margin: 0 }}>Recent Training Sessions</h2>
                    {sessions.length > 1 && (
                        <button
                            className="btn-compare-runs"
                            onClick={() => setShowCompare(true)}
                            disabled={compareIds.length < 2}
                            title={compareIds.length < 2 ? 'Tick at least two runs to compare' : 'Compare selected runs'}
                        >
                            ⚖️ Compare{compareIds.length > 0 ? ` (${compareIds.length})` : ''}
                        </button>
                    )}
                </div>
                {sessions.length === 0 ? (
                    <div className="empty-state">
                        <p>No training sessions yet. Head to the <a href="/lab">Lab</a> to train your first model!</p>
                    </div>
                ) : (
                    <div className="sessions-table">
                        <table>
                            <thead>
                                <tr>
                                    <th style={{ width: '34px', textAlign: 'center' }} title="Select to compare">⚖️</th>
                                    <th>Model</th>
                                    <th>Version</th>
                                    <th>Status</th>
                                    <th>Date</th>
                                    <th>Key Metric</th>
                                    <th>Trained Model</th>
                                    <th>Training Results</th>
                                    <th style={{ width: '50px', textAlign: 'center' }}>Replay</th>
                                    <th style={{ width: '50px', textAlign: 'center' }}>Delete</th>
                                </tr>
                            </thead>
                            <tbody>
                                {sessionsPage.pageItems.map((s) => (
                                    <tr key={s._id} className={compareIds.includes(s._id) ? 'row-selected-compare' : ''}>
                                        <td style={{ textAlign: 'center' }}>
                                            <input
                                                type="checkbox"
                                                checked={compareIds.includes(s._id)}
                                                onChange={() => toggleCompare(s._id)}
                                                title="Select for comparison"
                                            />
                                        </td>
                                        <td className="model-cell">
                                            <span className="model-badge" title={s.model_code}>{s.model_code}</span>
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
                                                    extension={getModelExtension(registry, s.model_code)}
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
                                            {s.status === 'completed' && isClassical(s.model_code) && (
                                                <button
                                                    className="btn-replay-session"
                                                    onClick={() => setPredictSession(s)}
                                                    title="Predict on new data with this model"
                                                    style={{ marginRight: 6 }}
                                                >
                                                    🔮
                                                </button>
                                            )}
                                            <button 
                                                className="btn-replay-session"
                                                onClick={() => handleReplaySession(s)}
                                                title="Reload this configuration"
                                            >
                                                <FontAwesomeIcon icon={faRedo} />
                                            </button>
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
                        <Pagination
                            page={sessionsPage.page}
                            totalPages={sessionsPage.totalPages}
                            totalItems={sessionsPage.totalItems}
                            pageSize={sessionsPage.pageSize}
                            onChange={sessionsPage.setPage}
                            unitLabel="sessions"
                        />
                    </div>
                )}
            </div>

            {/* Per-dataset leaderboard (D5) */}
            <Leaderboard sessions={sessions} />

            {/* Datasets */}
            <div className="dashboard-section">
                <h2>Your Datasets</h2>
                {datasets.length === 0 ? (
                    <div className="empty-state">
                        <p>No datasets uploaded yet.</p>
                    </div>
                ) : (
                    <>
                        <div className="datasets-grid">
                            {datasetsPage.pageItems.map((d) => (
                                <div className="dataset-card" key={d._id}>
                                    <span className="dataset-icon">📄</span>
                                    <div className="dataset-info">
                                        <span className="dataset-name" title={d.filename}>{truncateName(d.filename, 28)}</span>
                                        <span className="dataset-date">{new Date(d.uploaded_at).toLocaleDateString()}</span>
                                    </div>
                                    <span className="dataset-type">{d.file_type}</span>
                                </div>
                            ))}
                        </div>
                        <Pagination
                            page={datasetsPage.page}
                            totalPages={datasetsPage.totalPages}
                            totalItems={datasetsPage.totalItems}
                            pageSize={datasetsPage.pageSize}
                            onChange={datasetsPage.setPage}
                            unitLabel="datasets"
                        />
                    </>
                )}
            </div>

            {/* Run comparison modal (D2) */}
            {showCompare && (
                <RunComparison
                    sessions={sessions.filter(s => compareIds.includes(s._id))}
                    onClose={() => setShowCompare(false)}
                />
            )}

            {/* Predict-on-new-data modal (D3) */}
            {predictSession && (
                <PredictModal
                    session={predictSession}
                    onClose={() => setPredictSession(null)}
                />
            )}

            {/* First-run onboarding (D4) */}
            {showOnboarding && (
                <OnboardingModal onClose={() => setShowOnboarding(false)} />
            )}

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
                                style={{ background: 'var(--gradient-danger)' }}
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
