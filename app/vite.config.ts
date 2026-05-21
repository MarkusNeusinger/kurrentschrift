import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';

// Vite dev server proxies /api/* to the FastAPI backend so the frontend
// can use same-origin fetch calls (no CORS dance in dev). All app code
// hits /api/... — production swaps the proxy for a real reverse proxy.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
  preview: {
    port: 3000,
    host: true,
  },
});
