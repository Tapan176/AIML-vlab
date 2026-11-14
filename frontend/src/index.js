import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
// Shared form/button styles (auth-btn, auth-error, spinner-sm…) used across
// many pages. Loaded globally because pages are now code-split and would
// otherwise only get these once an auth page chunk happened to load.
import './components/Auth/Auth.css';
import './styles/responsive.css';
import App from './App';
import reportWebVitals from './reportWebVitals';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
