### Fixed

- **The API build context carried 451 MB it never used.** A `.dockerignore`
  pattern without a separator is matched against the path relative to the
  CONTEXT ROOT — Go's `filepath.Match`, not gitignore semantics — so the bare
  `node_modules` in the repo-root list covered only a top-level one, of which
  there is none. The 451 MB in `app/node_modules` travelled with every API
  build, and so did 216 `__pycache__` directories, `app/dist`, and the
  InkSight venv and weights under `tools/` (3.4 GB on a machine that has run
  route B). Every generated directory now carries `**/`: measured 339 MiB of
  context before, 44 MiB after, in a checkout without those weights.
  `.gcloudignore` needs no such fix — it uses gitignore semantics, where a bare
  name already matches at any depth.
- **The CSP hash extractor now reads HTML the way a browser does.** Its
  `</script>` pattern had no whitespace tolerance, so a legal `</script >`
  would have made it read on to the next closing tag and hash two scripts as
  one — the real first script would then have lost its hash and stopped
  running (CodeQL's `py/bad-tag-filter`). Alongside it, `"src=" in attrs`
  called `data-src=` external and `SRC = "…"` inline, and a commented-out
  `<script>` earned a hash for code that never runs. All three are fixed and
  pinned by a test; the two hashes `app/index.html` actually produces are
  unchanged, so the shipped policy is untouched.
