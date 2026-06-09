// Typed global configuration — the one place env vars and v1 hardcodes are
// read, so the rest of the app imports config instead of import.meta.env.

export const CONFIG = {
  /** Base path of the FastAPI backend (vite dev proxy / Cloudflare Worker in prod). */
  apiBase: '/api',
  /**
   * The single source the v1 UI is hardcoded to (multi-source is in the DB
   * schema but out of UI scope).
   */
  sourceId: 'loth-1866',
  /**
   * Local-dev write auth: in production the admin write endpoints are gated by
   * the Cloudflare Access cookie (forwarded by the CF Worker). For local dev
   * set VITE_ADMIN_TOKEN in app/.env (matching the API's ADMIN_TOKEN); it is
   * sent as X-Admin-Token. Unset in prod builds → cookie-based auth only.
   */
  adminToken: import.meta.env.VITE_ADMIN_TOKEN as string | undefined,
} as const;
