import React, { useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import OAuthSection from './OAuthSection';
import OtpVerify from './OtpVerify';
import './Auth.css';

const Login = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [otpEmail, setOtpEmail] = useState(null); // set → show OTP step
    const navigate = useNavigate();
    const [params] = useSearchParams();
    const nextUrl = params.get('next');
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

    const routeAfterAuth = (data) => {
        if (data?.user?.role === 'admin') navigate('/admin');
        else if (nextUrl) navigate(nextUrl);
        else navigate('/dashboard');
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const data = await login(email, password);
            if (data?.otp_required) {
                setOtpEmail(data.email || email);
            } else {
                routeAfterAuth(data);
            }
        } catch (err) {
            setError(err.message || 'Login failed. Please try again.');
        }
        setLoading(false);
    };

    if (otpEmail) {
        return (
            <OtpVerify
                email={otpEmail}
                purpose="login"
                onVerified={routeAfterAuth}
                onBack={() => setOtpEmail(null)}
            />
        );
    }

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

                <OAuthSection onError={setError} />

                <div className="auth-footer">
                    <p>Don't have an account? <Link to="/signup">Sign up</Link></p>
                </div>
            </div>
        </div>
    );
};

export default Login;
