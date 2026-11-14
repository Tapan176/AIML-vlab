import { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import { MotionConfig } from 'framer-motion';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { SubscriptionProvider } from './context/SubscriptionContext';
import { UIDialogProvider } from './context/UIDialog';
import Navbar from './components/Navbar/Navbar';
import ProtectedRoute, { PageLoader } from './components/Auth/ProtectedRoute';
import ErrorBoundary from './components/shared/ErrorBoundary';
import './App.css';

// Route-level code splitting: each page (and heavy deps like recharts, the
// Data Studio and the admin console) is downloaded only when first visited,
// instead of every visitor paying for the whole app on the landing page.
const LandingPage = lazy(() => import('./components/LandingPage/LandingPage'));
const Home = lazy(() => import('./components/Home/Home'));
const Login = lazy(() => import('./components/Auth/Login'));
const SignUp = lazy(() => import('./components/Auth/SignUp'));
const ForgotPassword = lazy(() => import('./components/Auth/ForgotPassword'));
const ResetPassword = lazy(() => import('./components/Auth/ResetPassword'));
const EditProfile = lazy(() => import('./components/Profile/EditProfile'));
const ProfilePage = lazy(() => import('./components/Profile/ProfilePage'));
const Settings = lazy(() => import('./components/Profile/Settings'));
const Dashboard = lazy(() => import('./components/Dashboard/Dashboard'));
const AboutUs = lazy(() => import('./components/AboutUs/AboutUs'));
const AdminLayout = lazy(() => import('./components/Admin/AdminLayout'));
const DatasetLibrary = lazy(() => import('./components/Dataset/DatasetLibrary'));
const DataStudio = lazy(() => import('./components/Studio/DataStudio'));
const PricingPage = lazy(() => import('./components/Subscription/PricingPage'));
const Checkout = lazy(() => import('./components/Subscription/Checkout'));
const NotFound = lazy(() => import('./components/shared/NotFound'));

const protectedRoutes = [
    ['/checkout', Checkout],
    ['/lab', Home],
    ['/datasets', DatasetLibrary],
    ['/studio', DataStudio],
    ['/profile', ProfilePage],
    ['/edit-profile', EditProfile],
    ['/settings', Settings],
    ['/dashboard', Dashboard],
];

function App() {
    return (
        <ThemeProvider>
            <AuthProvider>
                <Router>
                    <MotionConfig reducedMotion="user">
                    <UIDialogProvider>
                    <SubscriptionProvider>
                    <Navbar />
                    <main className="app-content">
                        <ErrorBoundary>
                            <Suspense fallback={<PageLoader />}>
                                <Routes>
                                    <Route path="/" element={<LandingPage />} />
                                    <Route path="/pricing" element={<PricingPage />} />
                                    <Route path="/about" element={<AboutUs />} />
                                    <Route path="/login" element={<Login />} />
                                    <Route path="/signup" element={<SignUp />} />
                                    <Route path="/forgot-password" element={<ForgotPassword />} />
                                    <Route path="/reset-password" element={<ResetPassword />} />
                                    {protectedRoutes.map(([path, Page]) => (
                                        <Route key={path} path={path} element={
                                            <ProtectedRoute><Page /></ProtectedRoute>
                                        } />
                                    ))}
                                    <Route path="/admin" element={
                                        <ProtectedRoute adminOnly><AdminLayout /></ProtectedRoute>
                                    } />
                                    <Route path="*" element={<NotFound />} />
                                </Routes>
                            </Suspense>
                        </ErrorBoundary>
                    </main>
                    </SubscriptionProvider>
                    </UIDialogProvider>
                    </MotionConfig>
                </Router>
            </AuthProvider>
        </ThemeProvider>
    );
}

export default App;
