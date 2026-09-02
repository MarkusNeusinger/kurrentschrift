import { fileURLToPath } from 'node:url';
// `vitest/config`, not `vite`: same defineConfig plus the types for the `test`
// block below.
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react-swc';

// Vite dev server proxies /api/* to the FastAPI backend so the frontend
// can use same-origin fetch calls (no CORS dance in dev). All app code
// hits /api/... — production swaps the proxy for a real reverse proxy.
export default defineConfig({
  plugins: [react()],
  resolve: {
    // Keep in sync with tsconfig.json "paths".
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
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
  test: {
    coverage: {
      provider: 'v8',
      // Without `include`, Vitest 4 reports only the modules a test happened to
      // import — which read as 82.7 % while the whole SPA source was at 18.1 %.
      // A coverage number that measures its own test list is worse than none.
      // (This is Vitest 4's replacement for the old `all: true`.)
      include: ['src/**/*.{ts,tsx}'],
      exclude: ['src/**/*.test.*', 'src/main.tsx', 'src/vite-env.d.ts'],
      reporter: ['text-summary', 'json'],
    },
  },
});
