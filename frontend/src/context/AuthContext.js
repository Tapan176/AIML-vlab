import { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
import { TOKEN_KEY } from '../constants';
import api, { clearCache, downloadFile } from '../services/api';

const AuthContext = createContext(null);

export const useAuth = () => {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error('useAuth must be used within AuthProvider');
    return ctx;
};

function readToken() {
    try { return localStorage.getItem(TOKEN_KEY); } catch (e) { return null; }
}

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(readToken());
    const [loading, setLoading] = useState(true);

    // Rehydrate user session from stored token
    const fetchCurrentUser = useCallback(async (storedToken) => {
        if (!storedToken) {
            setLoading(false);
            return;
        }
        try {
            // authGet de-dupes the StrictMode double-mount into one /me call and
            // does NOT hard-redirect on 401 (silent rehydrate just clears state).
            const data = await api.authGet('/me', storedToken, { force: true });
            setUser(data.user);
            setToken(storedToken);
        } catch (err) {
            // Only a definite auth failure drops the token; a network blip or
            // server restart must not log the user out.
            if (err.status === 401 || err.status === 403) {
                localStorage.removeItem(TOKEN_KEY);
                setToken(null);
                setUser(null);
            }
        }
        setLoading(false);
    }, []);

    useEffect(() => {
        fetchCurrentUser(token);

        // Keep auth state in sync across tabs (login/logout in another tab).
        const handleStorageChange = (e) => {
            if (e.key === TOKEN_KEY) {
                clearCache();
                if (e.newValue) {
                    fetchCurrentUser(e.newValue);
                } else {
                    setToken(null);
                    setUser(null);
                }
            }
        };

        window.addEventListener('storage', handleStorageChange);
        return () => window.removeEventListener('storage', handleStorageChange);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [fetchCurrentUser]);

    // Persist a freshly issued JWT + user into context + localStorage.
    const applySession = useCallback((data) => {
        clearCache();
        localStorage.setItem(TOKEN_KEY, data.token);
        setToken(data.token);
        if (data.user) setUser(data.user);
        return data;
    }, []);

    const clearSession = useCallback(() => {
        localStorage.removeItem(TOKEN_KEY);
        clearCache(); // so the next user never sees the previous user's cached lists
        setToken(null);
        setUser(null);
    }, []);

    const login = useCallback(async (email, password) => {
        const data = await api.publicPost('/login', { email, password });
        // OTP gate: backend confirmed credentials and emailed a code. Don't set
        // a session yet — the caller collects the OTP and calls verifyOtp().
        if (data.otp_required) return data;
        return applySession(data);
    }, [applySession]);

    const signup = useCallback(async (formData) => {
        const data = await api.publicPost('/signup', formData);
        if (data.otp_required) return data;
        return applySession(data);
    }, [applySession]);

    // Verify an emailed OTP to complete signup/login. purpose: 'signup'|'login'.
    const verifyOtp = useCallback(async (email, code, purpose) => {
        const data = await api.publicPost('/verify-otp', { email, code, purpose });
        return applySession(data);
    }, [applySession]);

    // Re-issue an OTP (subject to a server-side cooldown).
    const resendOtp = useCallback(async (email, purpose) => {
        try {
            return await api.publicPost('/resend-otp', { email, purpose });
        } catch (err) {
            err.retryAfter = err.data?.retry_after;
            throw err;
        }
    }, []);

    const logout = useCallback(() => {
        clearSession();
    }, [clearSession]);

    // Sign out on every device (revokes all tokens server-side, incl. this one).
    const logoutAll = useCallback(async () => {
        await api.post('/logout-all', {});
        clearSession();
    }, [clearSession]);

    const refreshUser = useCallback(async () => {
        const data = await api.get('/me', { force: true, ttl: 0 });
        setUser(data.user);
        return data.user;
    }, []);

    const updateProfile = useCallback(async (profileData) => {
        const data = await api.put('/update-profile', profileData);
        setUser(data.user);
        return data;
    }, []);

    const uploadProfilePhoto = useCallback(async (file) => {
        const formData = new FormData();
        formData.append('photo', file);
        const data = await api.uploadPut('/upload-profile-photo', formData);
        setUser(data.user);
        return data;
    }, []);

    // Changing the password revokes every other session; the server returns a
    // fresh token for this one, which we must store or we'd be logged out too.
    const changePassword = useCallback(async (oldPassword, newPassword) => {
        const data = await api.put('/change-password', { oldPassword, newPassword });
        if (data.token) applySession({ token: data.token });
        return data;
    }, [applySession]);

    const exportData = useCallback(() => downloadFile('/me/export', 'aiml-lab-export.json'), []);

    // Requires re-authentication: { password } for password accounts,
    // { confirm: 'DELETE' } for accounts created via Google/GitHub.
    const deleteAccount = useCallback(async (credentials = {}) => {
        const data = await api.delete('/delete-account', credentials);
        clearSession();
        return data;
    }, [clearSession]);

    const value = useMemo(() => ({
        user,
        token,
        loading,
        isAuthenticated: !!user && !!token,
        isAdmin: user?.role === 'admin',
        login,
        signup,
        verifyOtp,
        resendOtp,
        logout,
        logoutAll,
        refreshUser,
        applySession,
        updateProfile,
        uploadProfilePhoto,
        changePassword,
        exportData,
        deleteAccount,
    }), [user, token, loading, login, signup, verifyOtp, resendOtp, logout, logoutAll,
        refreshUser, applySession, updateProfile, uploadProfilePhoto, changePassword,
        exportData, deleteAccount]);

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};

export default AuthContext;
