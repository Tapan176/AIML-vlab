import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import constants from '../../constants';

import './signup.css';

export default function Signup() {
  const navigate = useNavigate();
  // const [isSignedUp, setIsSignedUp] = useState(false);

  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    countryCode: '+1',
    password: '',
    confirmPassword: '',
    termsAccepted: false
  });

  const [passwordsMatch, setPasswordsMatch] = useState(true); // State to track password match
  // const history = useHistory();

  const handleSubmit = async (event) => {
    event.preventDefault();

    // Validate form data
    if (!formData.termsAccepted) {
      alert('Please accept the terms and conditions.');
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      alert('Passwords do not match.');
      setPasswordsMatch(false);
      return;
    }

    // Perform signup logic here (e.g., API call)
    try {
      const response = await fetch(`${constants.API_BASE_URL}/signup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        // Signup successful, redirect to login page
        // setIsSignedUp(true);
        navigate('/login');
      } else {
        const errorData = await response.json();
        alert(errorData.message || 'Signup failed.');
      }
    } catch (error) {
      console.error('Signup error:', error);
      alert('Signup failed. Please try again.');
    }
  };

  // useEffect(() => {
  //   if (isSignedUp) {
  //     // Redirect to login page after signup
  //     window.location.href = '/login';
  //   }
  // }, [isSignedUp]);

  const handleInputChange = (event) => {
    const { id, value, type, checked } = event.target;
    setFormData((prevData) => ({
      ...prevData,
      [id]: type === 'checkbox' ? checked : value
    }));

    // Reset passwords match state when any of the password fields change
    if (id === 'password' || id === 'confirmPassword') {
      setPasswordsMatch(true);
    }
  };

  return (
    <div className="signupDiv mt-5">
            <h2>Signup</h2>
            <form onSubmit={handleSubmit}>
                <div className="mb-3">
                    <label htmlFor="firstName" className="form-label">First Name</label>
                    <input
                        type="text"
                        className="form-control"
                        id="firstName"
                        value={formData.firstName}
                        onChange={handleInputChange}
                        required
                    />
                </div>
                <div className="mb-3">
                    <label htmlFor="lastName" className="form-label">Last Name</label>
                    <input
                        type="text"
                        className="form-control"
                        id="lastName"
                        value={formData.lastName}
                        onChange={handleInputChange}
                        required
                    />
                </div>
                <div className="mb-3">
                    <label htmlFor="email" className="form-label">Email address</label>
                    <input
                        type="email"
                        className="form-control"
                        id="email"
                        value={formData.email}
                        onChange={handleInputChange}
                        required
                    />
                </div>
                <div className="mb-3">
                    <label htmlFor="phone" className="form-label">Phone Number</label>
                    <input
                        type="text"
                        className="form-control"
                        id="phone"
                        value={formData.phone}
                        onChange={handleInputChange}
                        required
                    />
                </div>
                <div className="mb-3">
                    <label htmlFor="countryCode" className="form-label">Country Code</label>
                    <select
                        className="form-select"
                        id="countryCode"
                        value={formData.countryCode}
                        onChange={handleInputChange}
                    >
                        <option value="+1">+1</option>
                        <option value="+91">+91</option>
                        {/* Add more options as needed */}
                    </select>
                </div>
                <div className="mb-3">
                    <label htmlFor="password" className="form-label">Password</label>
                    <input
                        type="password"
                        className="form-control"
                        id="password"
                        value={formData.password}
                        onChange={handleInputChange}
                        required
                    />
                </div>
                <div className="mb-3">
                    <label htmlFor="confirmPassword" className="form-label">Confirm Password</label>
                    <input
                        type="password"
                        className="form-control"
                        id="confirmPassword"
                        value={formData.confirmPassword}
                        onChange={handleInputChange}
                        required
                    />
                    {!passwordsMatch && <p className="text-danger">Passwords do not match.</p>}
                </div>
                <div className="mb-3 form-check">
                    <input
                        type="checkbox"
                        className="form-check-input"
                        id="termsAccepted"
                        checked={formData.termsAccepted}
                        onChange={handleInputChange}
                        required
                    />
                    <label className="form-check-label" htmlFor="termsAccepted">I accept the terms and conditions</label>
                </div>
                <button type="submit" className="btn btn-primary">Signup</button>
            </form>
        </div>
    );
}
