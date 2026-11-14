import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173, strictPort: true,
    // the engine (backend/, uvicorn on :8000) serves the API and results
    proxy: Object.fromEntries(['/scan', '/view', '/resolve', '/targets', '/object', '/live', '/bundles'].map((p) => [p, 'http://127.0.0.1:8000'])),
  },
  test: { environment: 'jsdom', clearMocks: true },
});
