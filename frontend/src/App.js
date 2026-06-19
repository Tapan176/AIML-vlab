import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import { Suspense, lazy } from 'react';
import { MotionConfig } from 'framer-motion';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { SubscriptionProvider } from './context/SubscriptionContext';
import { UIDialogProvider } from './context/UIDialog';
import Navbar from './components/Navbar/Navbar';
import ProtectedRoute from './components/Auth/ProtectedRoute';
import './App.css';

// Route screens are code-split so the initial bundle stays lean — each page's
// JS (and its heavy deps, e.g. charts on the Dashboard) loads on first
// navigation instead of upfront. Navbar + ProtectedRoute stay eager (they're
// part of the always-rendered shell).
const LandingPage = lazy(() => import('./components/LandingPage/LandingPage'));
const Home = lazy(() => import('./components/Home/Home'));
const Login = lazy(() => import('./components/Auth/Login'));
const SignUp = lazy(() => import('./components/Auth/SignUp'));
const ForgotPassword = lazy(() => import('./components/Auth/ForgotPassword'));
const EditProfile = lazy(() => import('./components/Profile/EditProfile'));
const ProfilePage = lazy(() => import('./components/Profile/ProfilePage'));
const Dashboard = lazy(() => import('./components/Dashboard/Dashboard'));
const AboutUs = lazy(() => import('./components/AboutUs/AboutUs'));
const Settings = lazy(() => import('./components/Profile/Settings'));
const AdminLayout = lazy(() => import('./components/Admin/AdminLayout'));
const DatasetLibrary = lazy(() => import('./components/Dataset/DatasetLibrary'));
const DataStudio = lazy(() => import('./components/Studio/DataStudio'));
const PricingPage = lazy(() => import('./components/Subscription/PricingPage'));
const Checkout = lazy(() => import('./components/Subscription/Checkout'));

function App() {
    return (
        <ThemeProvider>
            <AuthProvider>
                <Router>
                    <MotionConfig reducedMotion="user">
                    <UIDialogProvider>
                    <SubscriptionProvider>
                    <Navbar />
                    <div className="app-content">
                        <Suspense fallback={<div style={{ padding: '3rem', textAlign: 'center' }}>Loading…</div>}>
                        <Routes>
                            <Route path="/" element={<LandingPage />} />
                            <Route path="/pricing" element={<PricingPage />} />
                            <Route path="/checkout" element={
                                <ProtectedRoute>
                                    <Checkout />
                                </ProtectedRoute>
                            } />
                            <Route path="/lab" element={
                                <ProtectedRoute>
                                    <Home />
                                </ProtectedRoute>
                            } />
                            <Route path="/about" element={<AboutUs />} />
                            <Route path="/datasets" element={
                                <ProtectedRoute>
                                    <DatasetLibrary />
                                </ProtectedRoute>
                            } />
                            <Route path="/login" element={<Login />} />
                            <Route path="/signup" element={<SignUp />} />
                            <Route path="/forgot-password" element={<ForgotPassword />} />
                            <Route path="/studio" element={
                                <ProtectedRoute>
                                    <DataStudio />
                                </ProtectedRoute>
                            } />
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
                            <Route path="/settings" element={
                                <ProtectedRoute>
                                    <Settings />
                                </ProtectedRoute>
                            } />
                            <Route path="/dashboard" element={
                                <ProtectedRoute>
                                    <Dashboard />
                                </ProtectedRoute>
                            } />
                            <Route path="/admin" element={
                                <ProtectedRoute>
                                    <AdminLayout />
                                </ProtectedRoute>
                            } />
                        </Routes>
                        </Suspense>
                    </div>
                    </SubscriptionProvider>
                    </UIDialogProvider>
                    </MotionConfig>
                </Router>
            </AuthProvider>
        </ThemeProvider>
    );
}

export default App;
