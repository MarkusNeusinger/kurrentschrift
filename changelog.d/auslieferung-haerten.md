### Security

- **The site answers with security headers again — starting with a
  report-only CSP.** `kurrentschrift.ink` served none of the six usual headers
  (measured live: no `strict-transport-security`, no
  `content-security-policy`, no `x-content-type-options`, no
  `x-frame-options`, no `referrer-policy`), while the sister project carried
  all of them. `app/security-headers.conf` now holds them, written against the
  sources this site actually has — every one of them justified in the file.
  `script-src` gets by **without** `'unsafe-inline'`: the two inline scripts in
  `index.html` (the hero preload warmer and the Plausible stub) are allowed by
  sha256, and `tests/test_csp_policy.py` recomputes those hashes from
  `index.html` so the policy cannot silently drift from the page it protects.
  `style-src` keeps `'unsafe-inline'` because Emotion has no other path. HSTS
  is 180 days without `includeSubDomains` and without `preload`. The policy
  ships as `Content-Security-Policy-Report-Only` for one week and is switched
  by shortening the header name (#NNN).

- **The API host stamps `nosniff` and a `Referrer-Policy` on everything it
  answers.** `api.kurrentschrift.ink` is a second public host — SVG renders,
  crop images, JSON — and it carried neither. A lean ASGI middleware
  (`api/security_headers.py`) sits outside both gates, so the origin gate's 403
  and the rate limiter's 429 get them too. Deliberately no CSP there: `/docs`
  and `/redoc` load their bundles from a CDN and run inline scripts, so a
  policy worth setting would break the API's own documentation (#NNN).

- **Nothing named `.env` can reach a build context or a source upload any
  more.** `.dockerignore` listed `.env`, `.env.local` and `.env.*.local` — a
  `.env.staging` or `.env.production` fell straight through, and `app/` had no
  `.dockerignore` at all, so `COPY . .` carried the app's `.env` (which holds
  `VITE_ADMIN_TOKEN`) into an image layer. All three ignore files now say
  `.env*` (#NNN).

### Added

- **`POST /csp-report` — where the report-only week's findings land.** It
  counts and logs; it writes nothing, touches no table and returns no body. It
  understands both wire formats — `report-uri` posts one object, the Reporting
  API posts an array with camelCase fields — although only the first is
  declared: a browser walk measured that adding `report-to` makes Chromium
  ignore `report-uri` and then deliver nothing at all (200 s, no request), while
  without it the same violation arrived in under a second. A channel that
  silences the working one without replacing it is worse than no channel, so
  `report-to` waits until a report is seen arriving through it over HTTPS. One
  log line per *distinct* violation, repeats counted rather than
  repeated, the body capped at 64 KB, and the memo bounded — it is the one
  public write operation of this API, so it is named and argued in
  `tests/test_api_public_surface.py::PUBLIC_WRITES` rather than simply added
  (#NNN).

### Fixed

- **A deploy no longer hands returning visitors a white page.** The SPA shell
  carried no `Cache-Control` at all, only `Last-Modified`, so browsers cached
  it heuristically at ~10 % of its age; after a deploy that stale shell asked
  for `/assets/` hashes which `try_files … =404` no longer knows.
  `location = /index.html` now sets `no-cache` — deliberately not the sister
  project's `no-store`, so the measured 304-with-zero-bytes path survives; the
  reason stands as a comment, because the next sync will want to "fix" it back
  (#NNN).

- **`npm ci || npm install` in the app image is gone.** The fallback turned the
  one thing `npm ci` exists to catch — a missing or out-of-step lockfile — into
  a silent re-resolve, so the image could ship dependency versions no checkout
  and no CI run had ever seen (#NNN).

### Changed

- **The API image ships bytecode, which is ~2.2 s off every cold start.**
  `uv sync` ran without `--compile-bytecode` and `.dockerignore` excludes
  `__pycache__`, so every start compiled ~1,550 modules from source.
  `UV_COMPILE_BYTECODE=1` covers the venv and a `compileall` pass in the
  runtime stage covers `api/`, `core/` and `alembic/`. Measured with
  `-X importtime` on CPython 3.13, three runs each: 3,081–3,230 ms to import
  `api.main` without a bytecode cache against 909–1,038 ms with one. The
  builder now also pins uv itself and names its interpreter (`UV_PYTHON`,
  `UV_PYTHON_DOWNLOADS=never`) — the resolver was the last unpinned input of
  an otherwise fully pinned image. The cold-start comment in
  `api/cloudbuild.yaml` says what `min=1` did and did not fix, instead of
  implying the cold start is gone (#NNN).
