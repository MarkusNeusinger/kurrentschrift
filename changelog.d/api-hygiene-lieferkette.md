### Security

- **Four runtime packages of the API image were lifted out of 29 advisories.**
  `pip-audit` over `uv export --no-dev` — exactly the set `uv sync --frozen`
  installs in the image — reported starlette 1.0.0 (7, among them an
  unvalidated Host header before `request.url` and `request.form()` without
  `max_fields`/`max_part_size`), cryptography 48.0.0 (4, including exponential
  blowup on certificate chains, on the path that verifies the Access JWT),
  aiohttp 3.13.5 (14, among them an SNI bypass) and pyasn1 0.6.3 (4). Now
  starlette 1.6.0, cryptography 50.0.1, aiohttp 3.14.3, pyasn1 0.6.4;
  `pip-audit` after: 0. Exploitability here was limited — no `UploadFile`,
  `request.url` only ever `.path` — but a web framework six minor versions
  behind its fix is not something to argue case by case (#NNN).
- **`/write/word` is rate limited per client.** It is the one public read whose
  cost the caller sets: a unique text misses every cache by construction, and a
  unique 155-character request was measured at 0.80 s TTFB and 1,653,798 bytes,
  which with `--concurrency=15` saturates an instance and scales the service. An
  in-process token bucket (60 per minute, burst 20, `WRITE_RATE_LIMIT_PER_MIN`)
  answers 429 with `Retry-After` and `no-store`; `/write/glyphs` and the single
  glyph reads are bounded by the authored inventory and stay exempt. Keyed on
  the rightmost forwarded entry, because the leftmost is client-controlled and
  would let a caller both evade its own limit and poison a victim's bucket. In
  the process rather than at the edge on purpose: both Cloud Run services stand
  with `ingress=all`, so a Cloudflare rule is one `run.app` URL away from being
  bypassed while this one is not (#NNN).
- **The admin gate is pinned on every write operation, not on a sample.**
  `tests/test_api_public_surface.py` walked GET routes only, so a new POST, PUT,
  PATCH or DELETE that forgot `require_admin` fell through no net — the
  hand-kept list covered 11 of the 33. All 33 are now held against an explicitly
  EMPTY list of public write paths, so opening one has to be argued and named
  rather than forgotten (#NNN).

### Fixed

- **`/write/word` keeps the 4-decimal contract it documents.** The pipeline
  rounds what it stores, but composition multiplies those inputs apart again, so
  1,363 of the 3,777 numbers in `?text=lesen` shipped as
  `0.015600000000000001` — noise below the contract's own resolution, paid for
  in wire bytes on the API's most-requested origin route. A recursive walk at
  the serialisation boundary (`core/rounding.py`, called where the Cache-Control
  header is already set) puts it back: identity 46,440 → 30,570 bytes (−34.2 %),
  gzip-6 13,864 → 10,840 (−21.8 %), for 0.96 ms median over that payload against
  a ~52 ms compose. `core/compose.py`, the stored rows and the golden parity
  fixture are untouched, and the fixture rebuild's bit-exact gate rounds through
  the same function so it measures the row, never the serialisation (#NNN).
- **`apiFetch` gives up on a request that never answers.** It retried a
  502/503/504 and a thrown `TypeError` and nothing else, so a stalled connection
  or a Cloud Run boot past a minute produced neither — the spinner in
  `BootStatus` and `WrittenWord` span forever and the retry button never
  appeared. Every attempt now carries its own `AbortSignal.timeout` (20 s, 30 s
  for `/write/word`, overridable); an abort retries like a network error and,
  once the attempts are spent, surfaces as `ApiError(408)` instead of a raw
  `TimeoutError` (#NNN).
- **Five status constants Starlette renamed, and the warning filter that should
  have caught them.** Four `HTTP_422_UNPROCESSABLE_ENTITY` and one
  `HTTP_413_REQUEST_ENTITY_TOO_LARGE` sat in error paths although
  `filterwarnings` turns our own deprecations into errors: Starlette warns with
  `stacklevel=3`, so the warning is attributed to `fastapi.routing` and every
  module-anchored rule looks past it. A fourth rule matches on the message and
  pins neither module nor category — starlette 1.6 promptly moved the warning
  off `DeprecationWarning` onto its own class, which a category-pinned rule
  would have gone blind to. The 413 branch also gained the test it never had
  (#NNN).

### Changed

- **`/health` reports the running version, and the deploy asserts it.** The
  pre-traffic smoke in `api/cloudbuild.yaml` now compares it against the version
  in the build's own checkout — without it a smoke passes just as happily
  against an image this build did not produce. The same smoke stopped probing
  `n-medial`, a glyph key gone since migration 0017 that only ever passed
  because the admin gate answers 401 before the 404 (#NNN).
- **HEAD is answered everywhere, not only on `/seo-proxy`.** FastAPI's
  `@router.get` is GET-only, so link checkers and the assistants that preflight
  the two SVG assets `llms.txt` advertises got a 405 from the origin; they only
  looked healthy because the edge answers HEAD from a cached GET. anyplot's
  `HeadAsGetMiddleware` now does it app-wide, wrapped innermost so the crawler
  counter above it still sees the real method and does not book a probe as a
  read (#NNN).
- **`app/.nvmrc` and `engine-strict` name the Node version the build needs.**
  `package.json` has declared `engines.node >= 22` all along and nothing
  enforced it, so a Node 20 machine installed happily and then failed deep
  inside the build with `node: bad option: --experimental-strip-types` and no
  mention of a version (#NNN).
