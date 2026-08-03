// Typed global configuration — the one place env vars and v1 hardcodes are
// read, so the rest of the app imports config instead of import.meta.env.

export const CONFIG = {
  /**
   * API base for the ADMIN and local dev: the apex `/api` (Vite proxy in dev,
   * the Cloudflare Worker in prod). The apex `/api/*` is gated by Cloudflare
   * Access — that gate is what authorizes the admin's write endpoints, since
   * Access injects the verifying JWT only on this path.
   */
  apiBase: '/api',
  /**
   * API base for the PUBLIC pages in production. The apex `/api/*` above is
   * Access-gated: anonymous visitors get a 302 to the Cloudflare login, and
   * that cross-origin redirect fails the browser's CORS check — so public reads
   * cannot use it. They go straight to the open `api.` subdomain instead (same
   * data, no auth gate; writes there are still refused by `require_admin`).
   * Ignored in dev, where the resolver in lib/api/endpoints.ts falls back to
   * apiBase (the Vite proxy serves `/api` same-origin). Override per build with
   * VITE_PUBLIC_API_BASE.
   */
  // Trailing slashes are stripped so an override like `https://api.example/`
  // can't produce a double slash (`https://api.example//styles`) downstream.
  publicApiBase: ((import.meta.env.VITE_PUBLIC_API_BASE as string | undefined) ?? 'https://api.kurrentschrift.ink').replace(
    /\/+$/,
    '',
  ),
  /**
   * The source the PUBLIC pages (landing, worksheet, quiz) render — currently
   * the Sütterlin 1922 Ausgangsschrift chart. The admin is NOT bound to this:
   * it has a runtime source switcher (AdminContext, persisted per browser)
   * and only falls back to this id by default.
   */
  sourceId: 'suetterlin-1922',
  /**
   * Chart sources the admin's Vorlagen-Auswahl does NOT offer. Nothing is
   * deleted — the row, its chart bytes and its provenance stay exactly as they
   * are, and every API route keeps serving it; the workbench simply does not
   * put it up for choice while nobody is authoring on it.
   *
   * `petzendorfer-1889` is a SECOND Kurrent chart (another hand, ~57° vs.
   * Loth's ~50°) that was seeded ahead of time for the Kurrent digits row Loth
   * 1866 lacks (federmodelle.md §"Quellenlage"). Until that authoring starts,
   * Kurrent means Loth — two cards both labelled „Kurrent" only make the
   * entry choice ambiguous. Take the id out of this list to bring it back.
   */
  hiddenSourceIds: ['petzendorfer-1889'] as readonly string[],
  /**
   * Local-dev write auth: in production the admin write endpoints are gated by
   * the Cloudflare Access cookie (forwarded by the CF Worker). For local dev
   * set VITE_ADMIN_TOKEN in app/.env (matching the API's ADMIN_TOKEN); it is
   * sent as X-Admin-Token. Gated to dev builds so a token in the build env can
   * never end up embedded in a production bundle.
   */
  adminToken: import.meta.env.DEV ? (import.meta.env.VITE_ADMIN_TOKEN as string | undefined) : undefined,
} as const;
