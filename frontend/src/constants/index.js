import { API_URL as _API_URL } from '../config';

// Re-export so the rest of the app imports from constants, not config directly
export const API_URL = _API_URL;

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
    'Regression': ['simple_linear_regression', 'multivariable_linear_regression'],
    'Classification': ['logistic_regression', 'knn', 'decision_tree', 'random_forest', 'svm', 'naive_bayes'],
    'Clustering': ['k_means', 'dbscan'],
    'Neural Networks': ['ann', 'cnn', 'resnet', 'lstm', 'yolo'],
    'Ensemble': ['gradient_boosting', 'xgboost'],
    'NLP': ['sentiment_analysis', 'text_classification'],
    'Generative AI': ['stylegan'],
};

// Model categories icons for display
export const CATEGORY_ICONS = {
    'Regression': '📈',
    'Classification': '🎯',
    'Clustering': '🔮',
    'Neural Networks': '🕸️',
    'Ensemble': '🌲',
    'NLP': '📝',
    'Generative AI': '✨',
};

// Country codes used in the Signup form
export const COUNTRY_CODES = [
    { code: '+91', name: 'India (IN)' },
    { code: '+1', name: 'USA/Canada' },
    { code: '+44', name: 'UK (GB)' },
    { code: '+61', name: 'Australia (AU)' },
    { code: '+49', name: 'Germany (DE)' },
    { code: '+33', name: 'France (FR)' },
    { code: '+81', name: 'Japan (JP)' },
    { code: '+86', name: 'China (CN)' },
    { code: '+55', name: 'Brazil (BR)' },
    { code: '+7', name: 'Russia (RU)' },
    { code: '+27', name: 'South Africa (ZA)' },
    { code: '+971', name: 'UAE (AE)' },
    { code: '+65', name: 'Singapore (SG)' },
    { code: '+60', name: 'Malaysia (MY)' },
    { code: '+39', name: 'Italy (IT)' },
    { code: '+34', name: 'Spain (ES)' },
    { code: '+82', name: 'South Korea (KR)' },
    { code: '+92', name: 'Pakistan (PK)' },
    { code: '+880', name: 'Bangladesh (BD)' },
    { code: '+234', name: 'Nigeria (NG)' },
];

// Default export for backwards compatibility with model components
// that use: import constants from '../../constants'; constants.API_BASE_URL
const constants = { API_URL, API_BASE_URL: API_URL, ROUTES, MODEL_CATEGORIES };
export default constants;
