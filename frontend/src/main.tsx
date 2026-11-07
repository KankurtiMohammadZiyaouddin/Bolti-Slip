// src/main.tsx
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { registerSW } from 'virtual:pwa-register';
import App from './App';
import './index.css';

// Auto-register service worker for PWA offline shell & installability
registerSW({
  immediate: true,
  onRegisteredSW(swUrl, registration) {
    if (registration) {
      console.log('[PWA] Service Worker active:', swUrl, registration.scope);
    }
  },
  onRegisterError(error) {
    console.warn('[PWA] Service Worker registration failed:', error);
  },
});

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>
);
