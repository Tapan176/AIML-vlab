import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../context/AuthContext';
import './Auth.css';

/**
 * OTP entry step shown after a credential-validated signup/login when email
 * verification is enabled on the backend (OTP_ENABLED). Collects the emailed
 * code, verifies it, and on success calls onVerified(data) so the parent can
 * route the now-authenticated user.
 *
 * Props:
 *   email     - address the code was sent to
 *   purpose   - 'signup' | 'login'
 *   onVerified(data) - called with {user, token} after successful verification
 *   onBack    - optional: return to the credential form
 */
export default function OtpVerify({ email, purpose, onVerified, onBack }) {
    const { verifyOtp, resendOtp } = useAuth();
    const [code, setCode] = useState('');
    const [error, setError] = useState('');
    const [info, setInfo] = useState('');
    const [loading, setLoading] = useState(false);
    const [cooldown, setCooldown] = useState(0);
    const inputRef = useRef(null);

    useEffect(() => {
        if (inputRef.current) inputRef.current.focus();
    }, []);

    // Tick down the resend cooldown once it's set.
    useEffect(() => {
        if (cooldown <= 0) return undefined;
        const t = setInterval(() => setCooldown((c) => Math.max(0, c - 1)), 1000);
        return () => clearInterval(t);
    }, [cooldown]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setInfo('');
        const clean = code.replace(/\D/g, '');
        if (clean.length < 4) {
            setError('Enter the code from your email.');
            return;
        }
        setLoading(true);
        try {
            const data = await verifyOtp(email, clean, purpose);
            onVerified?.(data);
        } catch (err) {
            setError(humanize(err.message));
        }
        setLoading(false);
    };

    const handleResend = async () => {
        setError('');
        setInfo('');
        try {
            await resendOtp(email, purpose);
            setInfo('A new code has been sent to your email.');
            setCooldown(60);
        } catch (err) {
            if (err.retryAfter) {
                setCooldown(err.retryAfter);
                setError(`Please wait ${err.retryAfter}s before requesting a new code.`);
            } else {
                setError(humanize(err.message));
            }
        }
    };

    return (
        <div className="auth-container">
            <div className="auth-card">
                <div className="auth-header">
                    <h2>Verify your email</h2>
                    <p>We sent a verification code to <strong>{email}</strong></p>
                </div>

                {error && <div className="auth-error">{error}</div>}
                {info && <div className="auth-info">{info}</div>}

                <form onSubmit={handleSubmit} className="auth-form">
                    <div className="form-group">
                        <label htmlFor="otp-code">Verification code</label>
                        <input
                            id="otp-code"
                            ref={inputRef}
                            type="text"
                            inputMode="numeric"
                            autoComplete="one-time-code"
                            value={code}
                            onChange={(e) => setCode(e.target.value)}
                            placeholder="Enter 6-digit code"
                            maxLength={8}
                            className="otp-input"
                            required
                        />
                    </div>
                    <button type="submit" className="auth-btn" disabled={loading}>
                        {loading ? <span className="spinner-sm"></span> : 'Verify & continue'}
                    </button>
                </form>

                <div className="auth-actions" style={{ justifyContent: 'space-between' }}>
                    <button
                        type="button"
                        className="forgot-link link-button"
                        onClick={handleResend}
                        disabled={cooldown > 0}
                    >
                        {cooldown > 0 ? `Resend in ${cooldown}s` : 'Resend code'}
                    </button>
                    {onBack && (
                        <button type="button" className="forgot-link link-button" onClick={onBack}>
                            Use a different account
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}

function humanize(code) {
    const map = {
        otp_incorrect: 'That code is incorrect. Please try again.',
        otp_expired: 'That code has expired. Request a new one.',
        otp_not_found: 'No active code found. Request a new one.',
        otp_too_many_attempts: 'Too many attempts. Request a new code.',
        invalid_otp: 'Invalid code.',
        user_not_found: 'Account not found.',
    };
    return map[code] || code || 'Verification failed.';
}
