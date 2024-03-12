import React from 'react';
import { Link } from 'react-router-dom'; // Assuming you're using React Router

export default function Login() {
  return (
    <div>
      <h2>Login</h2>
      <form>
        <div className="mb-3">
          <label htmlFor="email" className="form-label">Email address</label>
          <input type="email" className="form-control" id="email" />
        </div>
        <div className="mb-3">
          <label htmlFor="password" className="form-label">Password</label>
          <input type="password" className="form-control" id="password" />
        </div>
        <div className="mb-3 form-check">
          <input type="checkbox" className="form-check-input" id="rememberMe" />
          <label className="form-check-label" htmlFor="rememberMe">Remember me</label>
        </div>
        <button type="submit" className="btn btn-primary">Login</button>
        <p>Forgot password? <Link to="/forgot-password">Reset here</Link></p> {/* Link to forgot password */}
        <Link to="/signup">Create New Account</Link>
      </form>
    </div>
  );
}
