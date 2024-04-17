import React, { useState } from 'react';
import { Link } from 'react-router-dom'; // Assuming you're using React Router for navigation
import ProfileDropdown from '../Profile/ProfileDropdown';

export default function Navbar({ isLoggedIn, user, onLogout }) {
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);

  const toggleProfileDropdown = () => {
    setShowProfileDropdown(!showProfileDropdown);
  };

  const closeProfileDropdown = () => {
    setShowProfileDropdown(false);
  };

  const handleLogout = () => {
    onLogout(); // Call the logout function passed from props
    closeProfileDropdown(); // Close the profile dropdown after logging out
  };

  return (
    <nav className="navbar navbar-expand-lg bg-body-tertiary">
      <div className="container-fluid">
        <Link className="navbar-brand" to="/">AI Model Hub</Link>
        <ul className="navbar-nav me-auto mb-2 mb-lg-0 flex-row">
          <li className="nav-item">
            <Link className="nav-link active" to="/">Home</Link>
          </li>
          <li className="nav-item">
            <Link className="nav-link" to="/about">About</Link>
          </li>
          <li className="nav-item">
            <Link className="nav-link" to="/contact-us">Contact Us</Link>
          </li>
        </ul>
        <form className="d-flex" role="search">
          <input className="form-control me-2" type="search" placeholder="Search" aria-label="Search" />
          <button className="btn btn-outline-success me-2" type="submit">Search</button>
        </form>
        {isLoggedIn ? (
          <div className="profile-icon" onClick={toggleProfileDropdown}>
            <img
              src={process.env.PUBLIC_URL + '/Assets/profile.jpg'}
              alt="Profile"
              className="rounded-circle"
              style={{ width: '40px', height: '40px', cursor: 'pointer' }}
            />
            {/* {showProfile && (
              <div className="profile-dropdown">
                <ProfileDropdown user={user} onLogout={onLogout} />
              </div>
            )} */}
          </div>
        ) : (
          <Link className="btn btn-primary mx-2" to="/login">Login/Register</Link>
        )}
      </div>
      {/* Render Profile dropdown outside the Navbar */}
      {showProfileDropdown && (
        <ProfileDropdown user={user} onLogout={handleLogout} onClose={() => setShowProfileDropdown(false)}/>
      )}

      {/* Add click event listener to close dropdown when clicking outside */}
      {showProfileDropdown && (
        <div className="overlay" onClick={closeProfileDropdown}></div>
      )}
    </nav>
  );
}
