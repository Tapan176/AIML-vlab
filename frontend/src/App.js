import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';

import Navbar from './components/Navbar/Navbar';
import About from './components/About/About';
import Home from './components/Home/Home';
import ContactUs from './components/ContactUs/ContactUs';
import Login from './components/Auth/Login';
import SignUp from './components/Auth/SignUp';
import EditProfile from './components/Profile/EditProfile';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState(null);

  const handleLogin = (userData) => {
    // Implement your login logic and set user state
    setIsLoggedIn(true);
    setUser(userData);
    // console.log(user)
  };

  const handleLogout = () => {
    // Implement your logout logic
    setIsLoggedIn(false);
    setUser(null);
  };

  return (
    <>
      <Router>
        <div>
          <Navbar isLoggedIn={isLoggedIn} user={user} onLogout={handleLogout} />
        </div>
        <div style={{ flex: 1 }}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/about" element={<About />} />
            <Route path="/contact-us" element={<ContactUs />} />
            <Route path="/login" element={<Login onLoginSuccess={handleLogin} />} />
            <Route path="/signup" element={<SignUp />} />
            <Route path="/edit-profile" element={<EditProfile user={user} />} />
          </Routes>
        </div>
      </Router>
    </>
  );
}

export default App;
