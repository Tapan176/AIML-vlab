import { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import api from '../../services/api';
import './Auth.css';

const MIN_LENGTH = 8;

/**
 * Landing page for the emailed reset link (/reset-password?token=…).
 * The token is single-use and expires; on success every existing session is
 * signed out, so the user signs in again with the new password.
 */
const ResetPassword = () => {
    const [params] = useSearchParams();
    const token = params.get('token') || '';
    const navigate = useNavigate();
    const [password, setPassword] = useState('');
    const [confirm, setConfirm] = useState('');
    const [error, setError] = useState('');
    const [done, setDone] = useState(false);
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        if (password.length < MIN_LENGTH) {
            setError(`Password must be at least ${MIN_LENGTH} characters.`);
            return;
        }
        if (password !== confirm) {
            setError('Passwords do not match.');
            return;
        }
        setLoading(true);
        try {
            await api.publicPost('/reset-password', { token, newPassword: password });
            setDone(true);
            setTimeout(() => navigate('/login'), 2500);
        } catch (err) {
            setError(err.message || 'Could not reset your password.');
        }
        setLoading(false);
    };

    if (!token) {
        return (
            <div className="auth-container">
                <div className="auth-card">
                    <div className="auth-header">
                        <h2>Invalid reset link</h2>
                        <p>This link is missing its reset token.</p>
                    </div>
                    <div className="auth-footer">
                        <p><Link to="/forgot-password">Request a new reset link</Link></p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="auth-container">
            <div className="auth-card">
                <div className="auth-header">
                    <h2>Choose a new password</h2>
                    <p>You'll be signed out of all devices after the change.</p>
                </div>
                {error && <div className="auth-error" role="alert">{error}</div>}
                {done ? (
                    <div className="auth-success" role="status">
                        Password updated. Redirecting you to sign in…
                    </div>
                ) : (
                    <form onSubmit={handleSubmit} className="auth-form">
                        <div className="form-group">
                            <label htmlFor="new-password">New password</label>
                            <input id="new-password" type="password" value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                autoComplete="new-password" minLength={MIN_LENGTH} required />
                        </div>
                        <div className="form-group">
                            <label htmlFor="confirm-password">Confirm new password</label>
                            <input id="confirm-password" type="password" value={confirm}
                                onChange={(e) => setConfirm(e.target.value)}
                                autoComplete="new-password" minLength={MIN_LENGTH} required />
                        </div>
                        <button type="submit" className="auth-btn" disabled={loading}>
                            {loading ? <span className="spinner-sm"></span> : 'Update password'}
                        </button>
                    </form>
                )}
                {error && (
                    <div className="auth-footer">
                        <p><Link to="/forgot-password">Request a new reset link</Link></p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ResetPassword;
