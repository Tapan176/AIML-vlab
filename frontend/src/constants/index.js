export const API_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:5050';

// Route constants
export const ROUTES = {
    HOME: '/',
    LAB: '/lab',
    LOGIN: '/login',
    SIGNUP: '/signup',
    FORGOT_PASSWORD: '/forgot-password',
    EDIT_PROFILE: '/edit-profile',
    DASHBOARD: '/dashboard',
};

// Model categories for display
export const MODEL_CATEGORIES = {
    regression: { label: 'Regression', icon: '📈' },
    classification: { label: 'Classification', icon: '🎯' },
    clustering: { label: 'Clustering', icon: '🔮' },
    neural_networks: { label: 'Neural Networks', icon: '🧠' },
};

// Default export for backwards compatibility with existing model components
// that use: import constants from '../../constants'; constants.API_BASE_URL
const constants = { API_URL, API_BASE_URL: API_URL, ROUTES, MODEL_CATEGORIES };
export default constants;
