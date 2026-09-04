### Security

- **`script-src` trades its two sha256 hashes for a per-request nonce.** nginx
  mints one from `$request_id` — 16 random bytes as 32 hex digits — sends it in
  the policy and stamps the same value onto every `<script>` tag of the shell
  with `sub_filter`, at server level so both routes to the shell carry it. The
  reason is a script this repository does not write: Cloudflare JavaScript
  Detections injects one into every HTML response at the edge, and its body
  carries a per-response ray id, so no hash can ever cover it — while a
  Free-plan zone with Bot Fight Mode on cannot turn the injection off. A nonce
  can cover it, because Cloudflare reads the response header and stamps its own
  script with what it finds; verified live on the sister site first, including
  the two scripts Cloudflare creates inside its hidden iframe. **The policy
  stays `Report-Only`** — the enforcing switch is still the one-word rename,
  and the report week now also measures whether the edge honours the nonce
  here.

- **The report week can now name the script it is reporting.** `script-src`
  asks for `'report-sample'` and `POST /csp-report` logs the sample beside the
  rest, through the same sanitiser and deliberately outside the dedupe key.
  Without it a browser sends an empty sample — measured on the live site — and
  a nonce policy collapses every inline violation onto one
  directive/blocked/document row, so the log could only say "an inline script
  was reported", which is not an answer to the question the week exists to ask.

### Changed

- **The SPA shell is `no-store` instead of `no-cache`.** Not the sister-file
  sync the old comment warned against, but a consequence of the nonce measured
  against this config: `sub_filter` clears `Last-Modified` and `ETag` on any
  response it rewrites, so the zero-byte 304 that `no-cache` was chosen for is
  gone either way — a conditional request now answers 200 with the full 17,287
  bytes. Same bytes as `no-store`, without its guarantee that no nonced
  document sits in a cache.

- **The frontend deploy smoke checks the nonce before promoting.** Ported from
  the sibling with its two corrections already in: `--compressed`, so a
  precompressed shell cannot sail past, and a 32-hex-digit match, so an empty
  nonce cannot agree with empty `nonce=""` tags. The static tests can only
  prove the config text agrees; this proves the candidate image's response
  does.

### Removed

- **The inline-script hash machinery, with the hashes it protected.**
  `tests/test_csp_policy.py` no longer carries the HTML tokenizer that
  recomputed the two sha256 values from `app/index.html`; five checks on the
  nonce path take its place, including the one that refuses any drift between
  the header's variable and the stamp's.
