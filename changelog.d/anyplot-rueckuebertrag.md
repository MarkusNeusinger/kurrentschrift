### Fixed

- **The API build context carried 451 MB it never used.** A `.dockerignore`
  pattern without a separator is matched against the path relative to the
  CONTEXT ROOT — Go's `filepath.Match`, not gitignore semantics — so the bare
  `node_modules` in the repo-root list covered only a top-level one, of which
  there is none. The 451 MB in `app/node_modules` travelled with every API
  build, and so did 216 `__pycache__` directories, `app/dist`, and the
  InkSight venv and weights under `tools/` (3.4 GB on a machine that has run
  route B). Every generated directory now carries `**/`: measured 339 MiB of
  context before, 44 MiB after, in a checkout without those weights. Beside
  them, the local-only payloads none of which the API Dockerfile copies — the
  corpora (up to 7.8 GB), the reserved own-hand strips, the NC-SA derivatives,
  the human-bench rounds and both benches' fixture and run trees. The same
  block goes into `.gcloudignore`, which runs BEFORE Docker sees anything: a
  manual `gcloud builds submit` would otherwise upload them regardless. Its
  syntax needed no `**/` — it is gitignore-shaped, where a bare name already
  matches at any depth.
- **The CSP hash extractor reads HTML with a tokenizer now, not a regex.** It
  decides which sha256 hashes the shipped policy must carry, and it was wrong
  in four ways that each put a wrong hash in: `</script>` as a literal misses
  the legal `</script >` and hashes two scripts as one (CodeQL's
  `py/bad-tag-filter`); `<script([^>]*)>` ends the start tag at a `>` inside a
  quoted attribute value; `"src=" in attrs` calls `data-src=` external and
  `SRC = "…"` inline; and a commented-out `<script>` earned a hash for code
  that never runs. `html.parser` settles all four, and a test pins them. The
  two hashes `app/index.html` actually produces are unchanged, so the shipped
  policy is untouched.
