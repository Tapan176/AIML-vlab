import { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import AdminDashboard from './AdminDashboard';
import UserManagement from './UserManagement';
import SessionsBrowser from './SessionsBrowser';
import FeedbackInbox from './FeedbackInbox';
import DatasetManager from './DatasetManager';
import './AdminDashboard.css';
import './Admin.css';

const TABS = [
    { key: 'overview', label: 'Overview' },
    { key: 'users', label: 'Users' },
    { key: 'sessions', label: 'Sessions' },
    { key: 'feedback', label: 'Feedback' },
    { key: 'datasets', label: 'Datasets' },
];

export default function AdminLayout() {
    const { user } = useAuth();
    const [activeTab, setActiveTab] = useState('overview');

    if (!user || user.role !== 'admin') {
        return (
            <div className="admin-denied">
                <h2>Access Denied</h2>
                <p>You do not have administrative privileges to view this page.</p>
            </div>
        );
    }

    const renderTab = () => {
        switch (activeTab) {
            case 'users':
                return <UserManagement />;
            case 'sessions':
                return <SessionsBrowser />;
            case 'feedback':
                return <FeedbackInbox />;
            case 'datasets':
                return <DatasetManager />;
            case 'overview':
            default:
                return <AdminDashboard />;
        }
    };

    return (
        <div className="admin-dashboard">
            <nav className="admin-tabs">
                {TABS.map((tab) => (
                    <button
                        key={tab.key}
                        className={`admin-tab${activeTab === tab.key ? ' active' : ''}`}
                        onClick={() => setActiveTab(tab.key)}
                    >
                        {tab.label}
                    </button>
                ))}
            </nav>
            {renderTab()}
        </div>
    );
}
