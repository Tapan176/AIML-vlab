import React, { useState, useEffect, useCallback } from 'react';
import { API_URL } from '../../constants';

// The OAuth popup HTML is served by the backend, so its postMessage arrives
// with the backend's origin. Only accept the token from that exact origin.
const API_ORIGIN = (() => {
    try { return new URL(API_URL).origin; } catch (e) { return ''; }
})();

/**
 * "Or continue with" social-login block, shared by the Login and SignUp pages.
 *
 * Renders one button per OAuth provider returned by GET /auth/providers — which
 * is empty unless GOOGLE_CLIENT_ID / GITHUB_CLIENT_ID are configured in the
 * backend .env, so nothing shows until OAuth is actually set up. The provider
 * login opens a popup; the backend posts the JWT back via postMessage (with a
 * URL-hash fallback when the popup is blocked).
 */
export default function OAuthSection({ onError }) {
    const [providers, setProviders] = useState([]);

    useEffect(() => {
        let active = true;
        fetch(`${API_URL}/auth/providers`)
            .then(res => res.json())
            .then(data => { if (active && data.providers) setProviders(data.providers); })
            .catch(() => {});
        return () => { active = false; };
    }, []);

    // Popup flow: backend postMessages the token back to this window.
    const handleOAuthMessage = useCallback((event) => {
        // Reject messages from any origin other than our backend — otherwise a
        // malicious page could inject a token and log the user into an attacker
        // account (login-CSRF / token injection).
        if (API_ORIGIN && event.origin !== API_ORIGIN) return;
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

    const startOAuth = (provider) => {
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
            .catch(() => onError && onError('OAuth login failed. Please try again.'));
    };

    if (providers.length === 0) return null;

    return (
        <div className="oauth-section">
            <div className="oauth-divider"><span>or continue with</span></div>
            <div className="oauth-buttons">
                {providers.map(provider => (
                    <button
                        key={provider.id}
                        type="button"
                        className="oauth-btn"
                        onClick={() => startOAuth(provider)}
                    >
                        <span className="oauth-icon">{provider.icon}</span>
                        <span>{provider.name}</span>
                    </button>
                ))}
            </div>
        </div>
    );
}
