import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import './ProfileDropdown.css';

const ProfileDropdown = ({ user, onLogout, onClose }) => {
  useEffect(() => {
    const handleClickOutside = (event) => {
      const dropdownContent = document.querySelector('.profile-dropdown-content');

      // Close dropdown if clicked outside of the dropdown content
      if (dropdownContent && !dropdownContent.contains(event.target)) {
        onClose();
      }
    };

    // Add event listener to handle clicks outside the dropdown
    document.addEventListener('mousedown', handleClickOutside);

    // Cleanup the event listener on component unmount
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [onClose]);

  return (
    <div className="profile-dropdown-container">
      <div className="profile-dropdown-content">
        <Link to="/edit-profile" className="dropdown-item">Edit Profile</Link>
        <button className="dropdown-item" onClick={onLogout}>Logout</button>
      </div>
    </div>
  );
};

export default ProfileDropdown;
