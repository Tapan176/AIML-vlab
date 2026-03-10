import { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlayCircle, faRobot, faFileAlt } from '@fortawesome/free-solid-svg-icons';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import constants, { API_URL } from '../../constants';
import './ProfilePage.css';

const ProfilePage = () => {
    const { user, isAuthenticated } = useAuth();
    const navigate = useNavigate();
    const [stats, setStats] = useState({ totalSessions: 0, modelsUsed: 0, datasetsUploaded: 0 });

    useEffect(() => {
        if (!isAuthenticated) {
            navigate('/login');
            return;
        }
        fetchStats();
    }, [isAuthenticated, navigate]);

    const fetchStats = async () => {
        try {
            const token = localStorage.getItem('aiml_token');
            const [sessionsRes, datasetsRes] = await Promise.all([
                fetch(`${constants.API_BASE_URL}/training-sessions`, { headers: { Authorization: `Bearer ${token}` } }),
                fetch(`${constants.API_BASE_URL}/user-datasets`, { headers: { Authorization: `Bearer ${token}` } }),
            ]);
            const sessionsData = sessionsRes.ok ? await sessionsRes.json() : { sessions: [] };
            const datasetsData = datasetsRes.ok ? await datasetsRes.json() : { datasets: [] };
            const sessions = sessionsData.sessions || [];
            const uniqueModels = new Set(sessions.map(s => s.model_code));
            setStats({
                totalSessions: sessions.length,
                modelsUsed: uniqueModels.size,
                datasetsUploaded: (datasetsData.datasets || []).length,
            });
        } catch (err) {
            console.error('Failed to load stats:', err);
        }
    };

    if (!user) return null;

    return (
        <div className="profile-page">
            <div className="profile-card">
                {user.profile_photo_id ? (
                    <img src={`${API_URL}/profile-photo/${user.profile_photo_id}`} alt="Profile" className="profile-avatar-large" style={{ objectFit: 'cover' }} />
                ) : user.profile_photo_url ? (
                    <img src={user.profile_photo_url} alt="Profile" className="profile-avatar-large" style={{ objectFit: 'cover' }} />
                ) : (
                    <div className="profile-avatar-large">
                        {user.first_name?.charAt(0)?.toUpperCase() || 'U'}
                    </div>
                )}
                <h1>{user.first_name} {user.last_name}</h1>
                <p className="profile-email">{user.email}</p>
                {user.phone && <p className="profile-phone">📱 {user.phone}</p>}

                <Link to="/edit-profile" className="btn-edit-profile">
                    ⚙️ Edit Profile
                </Link>
            </div>

            <div className="profile-stats">
                <div className="stat-card">
                    <span className="stat-icon">
                        <FontAwesomeIcon icon={faPlayCircle} />
                    </span>
                    <div className="stat-info">
                        <div className="stat-value">{stats.totalSessions}</div>
                        <div className="stat-label">Training Sessions</div>
                    </div>
                </div>
                <div className="stat-card">
                    <span className="stat-icon">
                        <FontAwesomeIcon icon={faRobot} />
                    </span>
                    <div className="stat-info">
                        <div className="stat-value">{stats.modelsUsed}</div>
                        <div className="stat-label">Models Used</div>
                    </div>
                </div>
                <div className="stat-card">
                    <span className="stat-icon">
                        <FontAwesomeIcon icon={faFileAlt} />
                    </span>
                    <div className="stat-info">
                        <div className="stat-value">{stats.datasetsUploaded}</div>
                        <div className="stat-label">Datasets</div>
                    </div>
                </div>
            </div>

            <div className="profile-actions">
                <Link to="/dashboard" className="profile-action-link">📊 View Dashboard</Link>
                <Link to="/lab" className="profile-action-link">🧪 Go to Lab</Link>
            </div>
        </div>
    );
};

export default ProfilePage;
