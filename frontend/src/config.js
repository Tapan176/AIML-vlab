/**
 * Application configuration.
 * All environment variables are read here and exported for use across the app.
 * Never use process.env directly outside of this file.
 */

export const API_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:5050';
