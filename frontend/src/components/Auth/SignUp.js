import React, { useState } from 'react';
// import { useHistory } from 'react-router-dom';

export default function Signup() {
  const [isSignedUp, setIsSignedUp] = useState(false);
  // const history = useHistory();

  const handleSubmit = (event) => {
    // Your signup logic goes here...
    // After successful signup, set isSignedUp to true
    setIsSignedUp(true);

    // Redirect to login page
    if (isSignedUp) {
      // history.push('/login');
    }
    
    // Prevent default form submission behavior
    event.preventDefault();
  };
  return (
    <div>
      <h2>Signup</h2>
      <form onSubmit={handleSubmit}>
        <div className="mb-3">
          <label htmlFor="firstName" className="form-label">First Name</label>
          <input type="text" className="form-control" id="firstName" />
        </div>
        <div className="mb-3">
          <label htmlFor="lastName" className="form-label">Last Name</label>
          <input type="text" className="form-control" id="lastName" />
        </div>
        <div className="mb-3">
          <label htmlFor="email" className="form-label">Email address</label>
          <input type="email" className="form-control" id="email" />
        </div>
        <div className="mb-3">
          <label htmlFor="phone" className="form-label">Phone Number</label>
          <input type="text" className="form-control" id="phone" />
        </div>
        <div className="mb-3">
          <label htmlFor="countryCode" className="form-label">Country Code</label>
          <select className="form-select" id="countryCode">
            <option value="+1">+1</option>
            <option value="+91">+91</option>
            {/* Add more options as needed */}
          </select>
        </div>
        <div className="mb-3">
          <label htmlFor="password" className="form-label">Password</label>
          <input type="password" className="form-control" id="password" />
        </div>
        <div className="mb-3">
          <label htmlFor="confirmPassword" className="form-label">Confirm Password</label>
          <input type="password" className="form-control" id="confirmPassword" />
        </div>
        <div className="mb-3 form-check">
          <input type="checkbox" className="form-check-input" id="termsAndConditions" />
          <label className="form-check-label" htmlFor="termsAndConditions">I accept the terms and conditions</label>
        </div>
        <button type="submit" className="btn btn-primary">Signup</button>
      </form>
    </div>
  );
}
