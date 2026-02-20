import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { API_URL } from '../constants';

const AuthContext = createContext(null);

export const useAuth = () => {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error('useAuth must be used within AuthProvider');
    return ctx;
};

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(localStorage.getItem('aiml_token'));
    const [loading, setLoading] = useState(true);

    // Rehydrate user session from stored token
    const fetchCurrentUser = useCallback(async (storedToken) => {
        if (!storedToken) {
            setLoading(false);
            return;
        }
        try {
            const res = await fetch(`${API_URL}/me`, {
                headers: { 'Authorization': `Bearer ${storedToken}` }
            });
            if (res.ok) {
                const data = await res.json();
                setUser(data.user);
                setToken(storedToken);
            } else {
                // Token expired or invalid
                localStorage.removeItem('aiml_token');
                setToken(null);
                setUser(null);
            }
        } catch (err) {
            console.error('Failed to rehydrate session:', err);
            localStorage.removeItem('aiml_token');
            setToken(null);
            setUser(null);
        }
        setLoading(false);
    }, []);

    useEffect(() => {
        fetchCurrentUser(token);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const login = async (email, password) => {
        const res = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Login failed');

        localStorage.setItem('aiml_token', data.token);
        setToken(data.token);
        setUser(data.user);
        return data;
    };

    const signup = async (formData) => {
        const res = await fetch(`${API_URL}/signup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Signup failed');

        localStorage.setItem('aiml_token', data.token);
        setToken(data.token);
        setUser(data.user);
        return data;
    };

    const logout = () => {
        localStorage.removeItem('aiml_token');
        setToken(null);
        setUser(null);
    };

    const updateProfile = async (profileData) => {
        const res = await fetch(`${API_URL}/update-profile`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(profileData)
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Update failed');
        setUser(data.user);
        return data;
    };

    const value = {
        user,
        token,
        loading,
        isAuthenticated: !!user && !!token,
        login,
        signup,
        logout,
        updateProfile,
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};

export default AuthContext;
