/**
 * Application configuration.
 * All environment variables are read here and exported for use across the app.
 * Never use process.env directly outside of this file.
 */

// Every backend blueprint is mounted under /api, so the default must include
// it (the old default pointed at the bare host and 404'd every request when
// no frontend/.env was present). A trailing slash is tolerated.
export const API_URL = (process.env.REACT_APP_API_URL || 'http://127.0.0.1:5050/api').replace(/\/+$/, '');
