import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import './EditProfile.css';

const Settings = () => {
    const { deleteAccount } = useAuth();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleDeleteAccount = async () => {
        if (window.confirm("Are you sure you want to delete your account? This action cannot be undone.")) {
            try {
                setLoading(true);
                await deleteAccount();
                navigate('/');
            } catch (err) {
                setError(err.message || 'Failed to delete account');
                setLoading(false);
            }
        }
    };

    return (
        <div className="edit-profile-container">
            <div className="edit-profile-card">
                <h2>Settings</h2>
                {error && <div className="auth-error">{error}</div>}

                <div className="settings-section">
                    <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem', fontSize: '0.9rem' }}>
                        Manage your account settings and preferences here. Currently, only account deletion is available.
                    </p>
                </div>

                <div className="danger-zone" style={{ marginTop: '2rem', paddingTop: '2rem', borderTop: '1px solid var(--border-color)' }}>
                    <h3 style={{ color: 'var(--error-color)', marginBottom: '1rem' }}>Danger Zone</h3>
                    <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem', fontSize: '0.9rem' }}>
                        Once you delete your account, there is no going back. Please be certain.
                    </p>
                    <button 
                        type="button" 
                        className="auth-btn outline danger" 
                        onClick={handleDeleteAccount} 
                        disabled={loading} 
                        style={{ width: 'auto', borderColor: 'var(--error-color)', color: 'var(--error-color)' }}
                    >
                        {loading ? <span className="spinner-sm"></span> : 'Delete Account'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Settings;
