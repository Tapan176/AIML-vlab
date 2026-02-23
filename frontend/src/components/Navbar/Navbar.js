import React, { useState, useRef, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import { API_URL } from '../../constants';
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
        // Use 'click' instead of 'mousedown' to ensure it aligns with onClick events
        // taking place in the React event lifecycle.
        document.addEventListener('click', handleClick);
        return () => document.removeEventListener('click', handleClick);
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
                    <Link to="/datasets" className={`nav-link ${isActive('/datasets') ? 'active' : ''}`}>Datasets</Link>
                    <Link to="/studio" className={`nav-link ${isActive('/studio') ? 'active' : ''}`}>Data Studio</Link>
                    <Link to="/about" className={`nav-link ${isActive('/about') ? 'active' : ''}`}>About</Link>
                    {isAuthenticated && (
                        <Link to="/dashboard" className={`nav-link ${isActive('/dashboard') ? 'active' : ''}`}>Dashboard</Link>
                    )}
                    {isAuthenticated && user?.role === 'admin' && (
                        <Link to="/admin" className={`nav-link ${isActive('/admin') ? 'active' : ''}`}>Admin Panel</Link>
                    )}
                </div>

                <div className="nav-actions">
                    <button className="theme-toggle" onClick={toggleTheme} title={isDark ? 'Switch to Light' : 'Switch to Dark'}>
                        {isDark ? '☀️' : '🌙'}
                    </button>

                    {isAuthenticated ? (
                        <div className="profile-menu" ref={dropdownRef}>
                            <button 
                                className="avatar-btn" 
                                type="button"
                                onClick={(e) => {
                                    console.log("Avatar clicked, toggling dropdown. Current state:", dropdownOpen);
                                    setDropdownOpen(prev => !prev);
                                }}
                            >
                                {user?.profile_photo_id ? (
                                    <img src={`${API_URL}/profile-photo/${user.profile_photo_id}`} alt="Avatar" className="avatar" style={{ objectFit: 'cover' }} />
                                ) : user?.profile_photo_url ? (
                                    <img src={user.profile_photo_url} alt="Avatar" className="avatar" style={{ objectFit: 'cover' }} />
                                ) : (
                                    <span className="avatar">
                                        {user?.first_name?.charAt(0)?.toUpperCase() || 'U'}
                                    </span>
                                )}
                            </button>
                            {dropdownOpen && (
                                <div className="nav-dropdown-menu">
                                    <div className="nav-dropdown-header">
                                        <span className="nav-dropdown-name">{user?.first_name} {user?.last_name}</span>
                                        <span className="nav-dropdown-email">{user?.email}</span>
                                    </div>
                                    <div className="nav-dropdown-divider"></div>
                                    <Link to="/profile" className="nav-dropdown-item" onClick={() => setDropdownOpen(false)}>👤 Profile</Link>
                                    <Link to="/settings" className="nav-dropdown-item" onClick={() => setDropdownOpen(false)}>⚙️ Settings</Link>
                                    <div className="nav-dropdown-divider"></div>
                                    <button className="nav-dropdown-item danger" onClick={() => { logout(); setDropdownOpen(false); }}>🚪 Logout</button>
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
