import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { SkyRegionDemo } from './pages/SkyRegionDemo';
import './styles/demo.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode><SkyRegionDemo /></StrictMode>,
);
