import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './pages/App';
import './styles/global.css';

// sky tiles + SPHEREx frames survive reloads (public/sw.js); not in `npm run dev`, where it would cache Vite's files
if ('serviceWorker' in navigator && import.meta.env.PROD) navigator.serviceWorker.register('/sw.js').catch(() => {});

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
