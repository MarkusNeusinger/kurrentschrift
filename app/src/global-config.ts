// Typed global configuration — the one place env vars and v1 hardcodes are
// read, so the rest of the app imports config instead of import.meta.env.

export const CONFIG = {
  /** Base path of the FastAPI backend (vite dev proxy / Cloudflare Worker in prod). */
  apiBase: '/api',
  /**
   * The single source the v1 UI is hardcoded to (multi-source is in the DB
   * schema but out of UI scope). Currently the Sütterlin 1922 Ausgangsschrift
   * chart; the Loth 1866 Kurrent chart is parked — flip back to 'loth-1866'
   * to resume authoring on it.
   */
  sourceId: 'suetterlin-1922',
  /**
   * Local-dev write auth: in production the admin write endpoints are gated by
   * the Cloudflare Access cookie (forwarded by the CF Worker). For local dev
   * set VITE_ADMIN_TOKEN in app/.env (matching the API's ADMIN_TOKEN); it is
   * sent as X-Admin-Token. Gated to dev builds so a token in the build env can
   * never end up embedded in a production bundle.
   */
  adminToken: import.meta.env.DEV ? (import.meta.env.VITE_ADMIN_TOKEN as string | undefined) : undefined,
} as const;
