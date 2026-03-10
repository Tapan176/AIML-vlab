import { useState } from 'react';
import { Link } from 'react-router-dom';
import './Auth.css';

const ForgotPassword = () => {
    const [email, setEmail] = useState('');
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setMessage('');
        setLoading(true);

        try {
            const res = await fetch('http://localhost:5050/forgot-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            });
            const data = await res.json();
            if (res.ok) {
                setMessage('Password reset instructions have been sent to your email.');
            } else {
                setError(data.error || 'Failed to send reset email');
            }
        } catch {
            setError('Network error. Please try again.');
        }
        setLoading(false);
    };

    return (
        <div className="auth-container">
            <div className="auth-card">
                <div className="auth-header">
                    <h2>Reset Password</h2>
                    <p>Enter your email to receive reset instructions</p>
                </div>
                {error && <div className="auth-error">{error}</div>}
                {message && <div className="auth-success">{message}</div>}
                <form onSubmit={handleSubmit} className="auth-form">
                    <div className="form-group">
                        <label htmlFor="reset-email">Email</label>
                        <input id="reset-email" type="email" value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="you@example.com" required />
                    </div>
                    <button type="submit" className="auth-btn" disabled={loading}>
                        {loading ? <span className="spinner-sm"></span> : 'Send Reset Link'}
                    </button>
                </form>
                <div className="auth-footer">
                    <p>Remember your password? <Link to="/login">Sign in</Link></p>
                </div>
            </div>
        </div>
    );
};

export default ForgotPassword;
