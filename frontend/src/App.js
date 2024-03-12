import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';

import Navbar from './components/Navbar/Navbar';
import About from './components/About/About';
import Home from './components/Home/Home';
import ContactUs from './components/ContactUs/ContactUs';
import Login from './components/Auth/Login';
import SignUp from './components/Auth/SignUp';
// import ShowDataset from './components/Dataset/ShowDataset';

function App() {
  return (
    <>
    <Router>
      <div>
        <Navbar />
      </div>
      <div style={{ flex: 1 }}>
        <Routes>
            <Route path="/" Component={Home} />
            <Route path="/about" Component={About} />
            <Route path="/contact-us" Component={ContactUs} />
            <Route path="/login" Component={Login} />
            <Route path="/signup" Component={SignUp} />
        </Routes>
      </div>
    </Router>
    </>
  );
}

export default App;
