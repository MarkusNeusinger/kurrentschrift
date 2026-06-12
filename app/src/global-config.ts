// Typed global configuration — the one place env vars and v1 hardcodes are
// read, so the rest of the app imports config instead of import.meta.env.

export const CONFIG = {
  /** Base path of the FastAPI backend (vite dev proxy / Cloudflare Worker in prod). */
  apiBase: '/api',
  /**
   * The source the PUBLIC pages (landing, worksheet, quiz) render — currently
   * the Sütterlin 1922 Ausgangsschrift chart. The admin is NOT bound to this:
   * it has a runtime source switcher (AdminContext, persisted per browser)
   * and only falls back to this id by default.
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
