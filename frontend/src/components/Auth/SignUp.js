import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { COUNTRY_CODES } from '../../constants';
import './Auth.css';

const SignUp = () => {
    const [formData, setFormData] = useState({
        firstName: '', lastName: '', email: '', password: '',
        confirmPassword: '', phone: '', countryCode: '+91', termsAccepted: false
    });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();
    const { signup } = useAuth();

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        if (formData.password !== formData.confirmPassword) {
            setError('Passwords do not match');
            return;
        }
        if (!formData.termsAccepted) {
            setError('Please accept the terms and conditions');
            return;
        }

        setLoading(true);
        try {
            await signup(formData);
            navigate('/lab');
        } catch (err) {
            setError(err.message || 'Signup failed');
        }
        setLoading(false);
    };

    return (
        <div className="auth-container">
            <div className="auth-card">
                <div className="auth-header">
                    <h2>Create Account</h2>
                    <p>Join ML Lab</p>
                </div>

                {error && <div className="auth-error">{error}</div>}

                <form onSubmit={handleSubmit} className="auth-form">
                    <div className="form-row">
                        <div className="form-group">
                            <label htmlFor="firstName">First Name</label>
                            <input type="text" id="firstName" name="firstName" value={formData.firstName}
                                onChange={handleChange} placeholder="John" required />
                        </div>
                        <div className="form-group">
                            <label htmlFor="lastName">Last Name</label>
                            <input type="text" id="lastName" name="lastName" value={formData.lastName}
                                onChange={handleChange} placeholder="Doe" required />
                        </div>
                    </div>
                    <div className="form-group">
                        <label htmlFor="signup-email">Email</label>
                        <input id="signup-email" name="email" type="email" value={formData.email}
                            onChange={handleChange} placeholder="you@example.com" required />
                    </div>
                    <div className="form-row">
                        <div className="form-group" style={{flex: '0 0 140px'}}>
                            <label htmlFor="countryCode">Code</label>
                            <select 
                                id="countryCode" 
                                name="countryCode" 
                                value={formData.countryCode}
                                onChange={handleChange} 
                                className="country-code-select"
                            >
                                {COUNTRY_CODES.map((c, idx) => (
                                    <option key={idx} value={c.code}>{c.code} {c.name}</option>
                                ))}
                            </select>
                        </div>
                        <div className="form-group">
                            <label htmlFor="phone">Phone</label>
                            <input type="tel" id="phone" name="phone" value={formData.phone}
                                onChange={handleChange} placeholder="1234567890" />
                        </div>
                    </div>
                    <div className="form-group">
                        <label htmlFor="signup-password">Password</label>
                        <input id="signup-password" name="password" type="password" value={formData.password}
                            onChange={handleChange} placeholder="Min 6 characters" required minLength={6} />
                    </div>
                    <div className="form-group">
                        <label htmlFor="confirmPassword">Confirm Password</label>
                        <input id="confirmPassword" name="confirmPassword" type="password" value={formData.confirmPassword}
                            onChange={handleChange} placeholder="Repeat password" required />
                    </div>
                    <div className="form-group checkbox-group">
                        <input type="checkbox" id="terms" name="termsAccepted"
                            checked={formData.termsAccepted} onChange={handleChange} />
                        <label htmlFor="terms">I accept the Terms & Conditions</label>
                    </div>
                    <button type="submit" className="auth-btn" disabled={loading}>
                        {loading ? <span className="spinner-sm"></span> : 'Create Account'}
                    </button>
                </form>

                <div className="auth-footer">
                    <p>Already have an account? <Link to="/login">Sign in</Link></p>
                </div>
            </div>
        </div>
    );
};

export default SignUp;
