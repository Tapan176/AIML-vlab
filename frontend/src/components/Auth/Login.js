import React, { useState } from 'react';
import { Link, useNavigate  } from 'react-router-dom';
import constants from '../../constants';

import './login.css';

const Login = ({ onLoginSuccess }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const navigate = useNavigate(); // Use the useNavigate hook for navigation

  const handleLogin = async (event) => {
    event.preventDefault();

    try {
      const response = await fetch(`${constants.API_BASE_URL}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
      });

      if (response.ok) {
        // Redirect to home page on successful login
        // sessionStorage.setItem('isLogin', 'true');
        const userData = await response.json();
        console.log(userData)
        onLoginSuccess(userData);
        navigate('/');
      } else {
        const errorMessage = await response.text();
        setError(errorMessage);
      }
    } catch (error) {
      console.error('Login Error:', error);
      setError('Failed to login. Please try again.');
    }
  };

  return (
    <div className="loginDiv mt-5">
            <h2>Login</h2>
            <form onSubmit={handleLogin}>
                <div className="mb-3">
                    <label htmlFor="email" className="form-label">Email address</label>
                    <input
                        type="email"
                        className="form-control"
                        id="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                    />
                </div>
                <div className="mb-3">
                    <label htmlFor="password" className="form-label">Password</label>
                    <input
                        type="password"
                        className="form-control"
                        id="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />
                </div>
                {error && <div className="alert alert-danger">{error}</div>}
                <button type="submit" className="btn btn-primary">Login</button>
                <p>Forgot password? <Link to="/forgot-password">Reset here</Link></p>
                <Link to="/signup" className="link">Create New Account</Link>
            </form>
        </div>
  );
};

export default Login;
