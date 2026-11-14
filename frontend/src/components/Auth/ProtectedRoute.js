import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export const PageLoader = ({ label = 'Loading...' }) => (
    <div className="loading-screen" role="status" aria-live="polite">
        <div className="spinner"></div>
        <p>{label}</p>
    </div>
);

/**
 * Gate a route behind authentication (and optionally the admin role).
 * Unauthenticated visitors are sent to /login with ?next= so they land back
 * on the page they asked for after signing in.
 */
const ProtectedRoute = ({ children, adminOnly = false }) => {
    const { isAuthenticated, isAdmin, loading } = useAuth();
    const location = useLocation();

    if (loading) return <PageLoader />;

    if (!isAuthenticated) {
        const next = encodeURIComponent(location.pathname + location.search);
        return <Navigate to={`/login?next=${next}`} replace />;
    }

    if (adminOnly && !isAdmin) {
        return (
            <div className="admin-denied">
                <h2>Access denied</h2>
                <p>You do not have administrative privileges to view this page.</p>
            </div>
        );
    }

    return children;
};

export default ProtectedRoute;
