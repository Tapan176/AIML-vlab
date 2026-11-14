import { Link } from 'react-router-dom';

export default function NotFound() {
    return (
        <div className="not-found">
            <h1>404</h1>
            <p>We couldn't find that page.</p>
            <Link to="/" className="auth-btn not-found-link">Back to home</Link>
        </div>
    );
}
