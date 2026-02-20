import React, { useState, useRef, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import './Navbar.css';

const Navbar = () => {
    const { user, isAuthenticated, logout } = useAuth();
    const { isDark, toggleTheme } = useTheme();
    const [dropdownOpen, setDropdownOpen] = useState(false);
    const dropdownRef = useRef(null);
    const location = useLocation();

    useEffect(() => {
        const handleClick = (e) => {
            if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
                setDropdownOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClick);
        return () => document.removeEventListener('mousedown', handleClick);
    }, []);

    const isActive = (path) => location.pathname === path;

    return (
        <nav className="navbar">
            <div className="nav-container">
                <Link to="/" className="nav-brand">
                    <span className="brand-icon">🧪</span>
                    <span className="brand-text">AIML<span className="brand-highlight">Lab</span></span>
                </Link>

                <div className="nav-links">
                    <Link to="/" className={`nav-link ${isActive('/') ? 'active' : ''}`}>Home</Link>
                    <Link to="/lab" className={`nav-link ${isActive('/lab') ? 'active' : ''}`}>Lab</Link>
                    <Link to="/about" className={`nav-link ${isActive('/about') ? 'active' : ''}`}>About</Link>
                    {isAuthenticated && (
                        <Link to="/dashboard" className={`nav-link ${isActive('/dashboard') ? 'active' : ''}`}>Dashboard</Link>
                    )}
                </div>

                <div className="nav-actions">
                    <button className="theme-toggle" onClick={toggleTheme} title={isDark ? 'Switch to Light' : 'Switch to Dark'}>
                        {isDark ? '☀️' : '🌙'}
                    </button>

                    {isAuthenticated ? (
                        <div className="profile-menu" ref={dropdownRef}>
                            <button className="avatar-btn" onClick={() => setDropdownOpen(!dropdownOpen)}>
                                <span className="avatar">
                                    {user?.first_name?.charAt(0)?.toUpperCase() || 'U'}
                                </span>
                            </button>
                            {dropdownOpen && (
                                <div className="dropdown-menu">
                                    <div className="dropdown-header">
                                        <span className="dropdown-name">{user?.first_name} {user?.last_name}</span>
                                        <span className="dropdown-email">{user?.email}</span>
                                    </div>
                                    <div className="dropdown-divider"></div>
                                    <Link to="/profile" className="dropdown-item" onClick={() => setDropdownOpen(false)}>👤 My Profile</Link>
                                    <Link to="/edit-profile" className="dropdown-item" onClick={() => setDropdownOpen(false)}>⚙️ Settings</Link>
                                    <Link to="/dashboard" className="dropdown-item" onClick={() => setDropdownOpen(false)}>📊 Dashboard</Link>
                                    <div className="dropdown-divider"></div>
                                    <button className="dropdown-item danger" onClick={() => { logout(); setDropdownOpen(false); }}>🚪 Logout</button>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="auth-buttons">
                            <Link to="/login" className="nav-btn-outline">Sign In</Link>
                            <Link to="/signup" className="nav-btn-primary">Sign Up</Link>
                        </div>
                    )}
                </div>
            </div>
        </nav>
    );
};

export default Navbar;
