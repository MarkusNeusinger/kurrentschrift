import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';

// Vite dev server proxies /api/* to the FastAPI backend so the frontend
// can use same-origin fetch calls (no CORS dance in dev). All app code
// hits /api/... — production swaps the proxy for a real reverse proxy.
export default defineConfig({
  plugins: [react()],
  resolve: {
    // Keep in sync with tsconfig.json "paths". URL instead of node:path so the
    // config needs no @types/node.
    alias: { '@': new URL('./src', import.meta.url).pathname },
  },
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
