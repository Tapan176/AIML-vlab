import React, { useState } from 'react';
import { useNavigate  } from 'react-router-dom';

import './editProfile.css';

const EditProfile = ({ user }) => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    firstName: user.first_name,
    lastName: user.last_name,
    phone: user.phone,
    email: user.email,
    countryCode: user.countryCode
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prevFormData) => ({
      ...prevFormData,
      [name]: value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    navigate('/');
    // Here you can implement logic to submit updated formData to server
    // console.log('Updated User Data:', formData);

    // Example: Call API to update user details with formData
    // updateUserData(formData);
  };

  return (
    <div className="editProfileDiv mt-5">
            <h2>Edit Profile</h2>
            <form onSubmit={handleSubmit}>
                <div className="mb-3">
                    <label htmlFor="firstName" className="form-label">First Name</label>
                    <input
                        type="text"
                        className="form-control"
                        id="firstName"
                        name="firstName"
                        value={formData.firstName}
                        onChange={handleChange}
                    />
                </div>
                <div className="mb-3">
                    <label htmlFor="lastName" className="form-label">Last Name</label>
                    <input
                        type="text"
                        className="form-control"
                        id="lastName"
                        name="lastName"
                        value={formData.lastName}
                        onChange={handleChange}
                    />
                </div>
                <div className="mb-3">
                    <label htmlFor="phone" className="form-label">Phone</label>
                    <input
                        type="text"
                        className="form-control"
                        id="phone"
                        name="phone"
                        value={formData.phone}
                        onChange={handleChange}
                    />
                </div>
                <div className="mb-3">
                    <label htmlFor="email" className="form-label">Email</label>
                    <input
                        type="email"
                        className="form-control"
                        id="email"
                        name="email"
                        value={formData.email}
                        onChange={handleChange}
                    />
                </div>
                <div className="mb-3">
                    <label htmlFor="countryCode" className="form-label">Country Code</label>
                    <input
                        type="text"
                        className="form-control"
                        id="countryCode"
                        name="countryCode"
                        value={formData.countryCode}
                        onChange={handleChange}
                    />
                </div>
                <button type="submit" className="btn btn-primary">Update Profile</button>
            </form>
        </div>
    );
};

export default EditProfile;
