import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import Navbar from './components/Navbar/Navbar';
import LandingPage from './components/LandingPage/LandingPage';
import Home from './components/Home/Home';
import Login from './components/Auth/Login';
import Signup from './components/Auth/Signup';
import ForgotPassword from './components/Auth/ForgotPassword';
import EditProfile from './components/Profile/EditProfile';
import ProfilePage from './components/Profile/ProfilePage';
import Dashboard from './components/Dashboard/Dashboard';
import AboutUs from './components/AboutUs/AboutUs';
import ProtectedRoute from './components/Auth/ProtectedRoute';
import './App.css';

function App() {
    return (
        <ThemeProvider>
            <AuthProvider>
                <Router>
                    <Navbar />
                    <div className="app-content">
                        <Routes>
                            <Route path="/" element={<LandingPage />} />
                            <Route path="/lab" element={<Home />} />
                            <Route path="/about" element={<AboutUs />} />
                            <Route path="/login" element={<Login />} />
                            <Route path="/signup" element={<Signup />} />
                            <Route path="/forgot-password" element={<ForgotPassword />} />
                            <Route path="/profile" element={
                                <ProtectedRoute>
                                    <ProfilePage />
                                </ProtectedRoute>
                            } />
                            <Route path="/edit-profile" element={
                                <ProtectedRoute>
                                    <EditProfile />
                                </ProtectedRoute>
                            } />
                            <Route path="/dashboard" element={
                                <ProtectedRoute>
                                    <Dashboard />
                                </ProtectedRoute>
                            } />
                        </Routes>
                    </div>
                </Router>
            </AuthProvider>
        </ThemeProvider>
    );
}

export default App;
