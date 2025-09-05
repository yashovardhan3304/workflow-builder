import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

// Silence benign ResizeObserver warnings in Chrome
const silenceResizeObserver = (e) => {
  if (e?.message && (e.message.includes('ResizeObserver loop') || e.message.includes('ResizeObserver'))) {
    e.stopImmediatePropagation();
  }
};
window.addEventListener('error', silenceResizeObserver);
window.addEventListener('unhandledrejection', silenceResizeObserver);

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
