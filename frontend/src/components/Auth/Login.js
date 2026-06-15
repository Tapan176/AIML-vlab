import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { API_URL } from '../../constants';
import './Auth.css';

const Login = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [oauthProviders, setOauthProviders] = useState([]);
    const navigate = useNavigate();
    const { login, isAuthenticated, user } = useAuth();

    // Auto-redirect if already logged in across tabs
    React.useEffect(() => {
        if (isAuthenticated && user) {
            if (user.role === 'admin') {
                navigate('/admin');
            } else {
                navigate('/lab');
            }
        }
    }, [isAuthenticated, user, navigate]);

    // Fetch available OAuth providers
    useEffect(() => {
        fetch(`${API_URL}/auth/providers`)
            .then(res => res.json())
            .then(data => {
                if (data.providers) setOauthProviders(data.providers);
            })
            .catch(() => {});
    }, []);

    // Listen for OAuth callback messages (popup flow: backend postMessages the token)
    const handleOAuthMessage = useCallback((event) => {
        if (event.data && event.data.type === 'OAUTH_LOGIN' && event.data.token) {
            localStorage.setItem('aiml_token', event.data.token);
            window.location.href = '/dashboard';
        }
    }, []);

    useEffect(() => {
        window.addEventListener('message', handleOAuthMessage);
        return () => window.removeEventListener('message', handleOAuthMessage);
    }, [handleOAuthMessage]);

    // Redirect fallback (popup blocked): backend lands us on /login#oauth_token=...
    useEffect(() => {
        const hash = window.location.hash || '';
        const match = hash.match(/oauth_token=([^&]+)/);
        if (match) {
            localStorage.setItem('aiml_token', decodeURIComponent(match[1]));
            window.history.replaceState(null, '', window.location.pathname); // scrub token from URL
            window.location.href = '/dashboard';
        }
    }, []);

    const handleOAuthLogin = (provider) => {
        fetch(`${API_URL}/auth/${provider.id}/login`)
            .then(res => res.json())
            .then(data => {
                if (data.url) {
                    const width = 600, height = 700;
                    const left = window.screenX + (window.outerWidth - width) / 2;
                    const top = window.screenY + (window.outerHeight - height) / 2;
                    window.open(data.url, 'oauth', `width=${width},height=${height},left=${left},top=${top}`);
                }
            })
            .catch(err => setError('OAuth login failed. Please try again.'));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const data = await login(email, password);
            if (data?.user?.role === 'admin') {
                navigate('/admin');
            } else {
                navigate('/dashboard');
            }
        } catch (err) {
            setError(err.message || 'Login failed. Please try again.');
        }
        setLoading(false);
    };

    return (
        <div className="auth-container">
            <div className="auth-card">
                <div className="auth-header">
                    <h2>Welcome Back</h2>
                    <p>Sign in to your AI/ML Lab account</p>
                </div>

                {error && <div className="auth-error">{error}</div>}

                <form onSubmit={handleSubmit} className="auth-form">
                    <div className="form-group">
                        <label htmlFor="email">Email</label>
                        <input
                            id="email"
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="you@example.com"
                            required
                        />
                    </div>
                    <div className="form-group">
                        <label htmlFor="password">Password</label>
                        <input
                            id="password"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Enter your password"
                            required
                        />
                    </div>
                    <div className="auth-actions">
                        <Link to="/forgot-password" className="forgot-link">Forgot password?</Link>
                    </div>
                    <button type="submit" className="auth-btn" disabled={loading}>
                        {loading ? <span className="spinner-sm"></span> : 'Sign In'}
                    </button>
                </form>

                {oauthProviders.length > 0 && (
                    <div className="oauth-section">
                        <div className="oauth-divider"><span>or continue with</span></div>
                        <div className="oauth-buttons">
                            {oauthProviders.map(provider => (
                                <button
                                    key={provider.id}
                                    type="button"
                                    className="oauth-btn"
                                    onClick={() => handleOAuthLogin(provider)}
                                >
                                    <span className="oauth-icon">{provider.icon}</span>
                                    <span>{provider.name}</span>
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                <div className="auth-footer">
                    <p>Don't have an account? <Link to="/signup">Sign up</Link></p>
                </div>
            </div>
        </div>
    );
};

export default Login;
