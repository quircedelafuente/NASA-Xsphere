import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Dev: data and the live engine come from the Python API (backend/, uvicorn on :8000).
// /bundles is served by the engine's adapter (pre-built + live bundles, meta/spectrum/flags filled in).
const ENGINE = 'http://127.0.0.1:8000';
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: Object.fromEntries(['/bundles', '/live', '/reports', '/view', '/scan', '/resolve', '/targets', '/object', '/lib3d', '/explore']
      .map((p) => [p, ENGINE])),
  },
});
